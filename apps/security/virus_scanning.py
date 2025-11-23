"""
Virus Scanning for File Uploads

Provides virus scanning capabilities using ClamAV or Azure Defender for Storage
"""

import logging
import hashlib
import subprocess
from typing import Optional, Tuple, Dict
from pathlib import Path
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

class VirusScanConfig:
    """Configuration for virus scanning"""

    # Scanner type: 'clamav', 'azure_defender', 'disabled'
    SCANNER_TYPE = getattr(settings, 'VIRUS_SCANNER_TYPE', 'clamav')

    # ClamAV settings
    CLAMAV_SOCKET = getattr(settings, 'CLAMAV_SOCKET', '/var/run/clamav/clamd.ctl')
    CLAMAV_HOST = getattr(settings, 'CLAMAV_HOST', 'localhost')
    CLAMAV_PORT = getattr(settings, 'CLAMAV_PORT', 3310)

    # File size limits (in bytes)
    MAX_SCAN_SIZE = getattr(settings, 'MAX_VIRUS_SCAN_SIZE', 100 * 1024 * 1024)  # 100 MB

    # Cache settings
    CACHE_CLEAN_FILES = getattr(settings, 'CACHE_CLEAN_FILES', True)
    CACHE_TIMEOUT = getattr(settings, 'CLEAN_FILE_CACHE_TIMEOUT', 3600 * 24)  # 24 hours

    # Quarantine settings
    QUARANTINE_INFECTED = getattr(settings, 'QUARANTINE_INFECTED_FILES', True)
    QUARANTINE_DIR = getattr(settings, 'QUARANTINE_DIR', '/tmp/quarantine')


# =============================================================================
# Scan Result
# =============================================================================

class ScanResult:
    """Result of a virus scan"""

    def __init__(
        self,
        is_clean: bool,
        threat_name: Optional[str] = None,
        scanner: str = 'unknown',
        scan_duration: float = 0.0,
        file_hash: Optional[str] = None
    ):
        self.is_clean = is_clean
        self.threat_name = threat_name
        self.scanner = scanner
        self.scan_duration = scan_duration
        self.file_hash = file_hash

    @property
    def is_infected(self):
        """Check if file is infected"""
        return not self.is_clean

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'is_clean': self.is_clean,
            'is_infected': self.is_infected,
            'threat_name': self.threat_name,
            'scanner': self.scanner,
            'scan_duration': self.scan_duration,
            'file_hash': self.file_hash
        }

    def __str__(self):
        if self.is_clean:
            return f"Clean (scanned by {self.scanner})"
        return f"Infected: {self.threat_name} (detected by {self.scanner})"


# =============================================================================
# ClamAV Scanner
# =============================================================================

class ClamAVScanner:
    """
    ClamAV virus scanner implementation

    Requires ClamAV to be installed and running:
        sudo apt-get install clamav clamav-daemon
        sudo systemctl start clamav-daemon
    """

    @staticmethod
    def is_available() -> bool:
        """Check if ClamAV is available"""
        try:
            import pyclamd
            cd = pyclamd.ClamdUnixSocket(VirusScanConfig.CLAMAV_SOCKET)
            return cd.ping()
        except Exception as e:
            logger.warning(f'ClamAV not available: {str(e)}')
            return False

    @staticmethod
    def scan_file(file_path: str) -> ScanResult:
        """
        Scan a file using ClamAV

        Args:
            file_path: Path to file to scan

        Returns:
            ScanResult instance
        """
        import time
        start_time = time.time()

        try:
            import pyclamd

            # Connect to ClamAV
            cd = pyclamd.ClamdUnixSocket(VirusScanConfig.CLAMAV_SOCKET)

            # Scan file
            result = cd.scan_file(file_path)

            duration = time.time() - start_time

            if result is None:
                # File is clean
                return ScanResult(
                    is_clean=True,
                    scanner='clamav',
                    scan_duration=duration
                )
            else:
                # File is infected
                threat_name = result[file_path][1]
                logger.warning(f'Infected file detected: {file_path} - {threat_name}')

                return ScanResult(
                    is_clean=False,
                    threat_name=threat_name,
                    scanner='clamav',
                    scan_duration=duration
                )

        except ImportError:
            logger.error('pyclamd library not installed. Run: pip install pyclamd')
            return ScanResult(
                is_clean=True,  # Allow file if scanner unavailable
                scanner='clamav (unavailable)',
                scan_duration=0.0
            )
        except Exception as e:
            logger.error(f'ClamAV scan error: {str(e)}')
            return ScanResult(
                is_clean=True,  # Allow file on error
                scanner='clamav (error)',
                scan_duration=0.0
            )

    @staticmethod
    def scan_stream(file_data: bytes) -> ScanResult:
        """
        Scan file data from memory

        Args:
            file_data: File content as bytes

        Returns:
            ScanResult instance
        """
        import time
        start_time = time.time()

        try:
            import pyclamd

            cd = pyclamd.ClamdUnixSocket(VirusScanConfig.CLAMAV_SOCKET)
            result = cd.scan_stream(file_data)

            duration = time.time() - start_time

            if result is None:
                return ScanResult(
                    is_clean=True,
                    scanner='clamav',
                    scan_duration=duration
                )
            else:
                threat_name = result['stream'][1]
                logger.warning(f'Infected data detected: {threat_name}')

                return ScanResult(
                    is_clean=False,
                    threat_name=threat_name,
                    scanner='clamav',
                    scan_duration=duration
                )

        except Exception as e:
            logger.error(f'ClamAV stream scan error: {str(e)}')
            return ScanResult(
                is_clean=True,
                scanner='clamav (error)',
                scan_duration=0.0
            )


# =============================================================================
# Azure Defender Scanner
# =============================================================================

class AzureDefenderScanner:
    """
    Azure Defender for Storage implementation

    Requires Azure Storage with Defender enabled
    """

    @staticmethod
    def is_available() -> bool:
        """Check if Azure Defender is configured"""
        try:
            from azure.storage.blob import BlobServiceClient
            connection_string = getattr(settings, 'AZURE_STORAGE_CONNECTION_STRING', None)
            return connection_string is not None
        except ImportError:
            return False

    @staticmethod
    def scan_file(file_path: str) -> ScanResult:
        """
        Scan file using Azure Defender

        Note: Azure Defender scans files asynchronously after upload.
        This method uploads the file to a scan container and checks the result.

        Args:
            file_path: Path to file to scan

        Returns:
            ScanResult instance
        """
        import time
        start_time = time.time()

        try:
            from azure.storage.blob import BlobServiceClient

            # Get connection string
            connection_string = settings.AZURE_STORAGE_CONNECTION_STRING

            # Create blob client
            blob_service = BlobServiceClient.from_connection_string(connection_string)

            # Upload to scan container
            container_name = 'virus-scan'
            blob_name = f'scan_{Path(file_path).name}'

            blob_client = blob_service.get_blob_client(
                container=container_name,
                blob=blob_name
            )

            with open(file_path, 'rb') as data:
                blob_client.upload_blob(data, overwrite=True)

            # Check malware scan result (from blob metadata)
            properties = blob_client.get_blob_properties()
            metadata = properties.get('metadata', {})

            duration = time.time() - start_time

            # Azure Defender sets 'Malware Scanning Scan Result' metadata
            scan_result = metadata.get('Malware Scanning Scan Result', 'No threats found')

            if scan_result == 'No threats found':
                return ScanResult(
                    is_clean=True,
                    scanner='azure_defender',
                    scan_duration=duration
                )
            else:
                logger.warning(f'Azure Defender detected threat: {scan_result}')
                return ScanResult(
                    is_clean=False,
                    threat_name=scan_result,
                    scanner='azure_defender',
                    scan_duration=duration
                )

        except Exception as e:
            logger.error(f'Azure Defender scan error: {str(e)}')
            return ScanResult(
                is_clean=True,
                scanner='azure_defender (error)',
                scan_duration=0.0
            )


# =============================================================================
# Unified Virus Scanner
# =============================================================================

class VirusScanner:
    """
    Unified virus scanner that uses configured scanner
    """

    @staticmethod
    def get_file_hash(file_path: str) -> str:
        """
        Calculate SHA256 hash of file

        Args:
            file_path: Path to file

        Returns:
            SHA256 hash string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b''):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @staticmethod
    def get_cached_result(file_hash: str) -> Optional[ScanResult]:
        """
        Get cached scan result

        Args:
            file_hash: SHA256 hash of file

        Returns:
            ScanResult if cached, None otherwise
        """
        if not VirusScanConfig.CACHE_CLEAN_FILES:
            return None

        cache_key = f'virus_scan_{file_hash}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return ScanResult(
                is_clean=cached_data['is_clean'],
                threat_name=cached_data.get('threat_name'),
                scanner=f"{cached_data['scanner']} (cached)",
                scan_duration=0.0,
                file_hash=file_hash
            )

        return None

    @staticmethod
    def cache_result(file_hash: str, result: ScanResult):
        """Cache scan result"""
        if not VirusScanConfig.CACHE_CLEAN_FILES:
            return

        cache_key = f'virus_scan_{file_hash}'
        cache.set(cache_key, result.to_dict(), timeout=VirusScanConfig.CACHE_TIMEOUT)

    @staticmethod
    def quarantine_file(file_path: str, threat_name: str):
        """
        Move infected file to quarantine

        Args:
            file_path: Path to infected file
            threat_name: Name of detected threat
        """
        if not VirusScanConfig.QUARANTINE_INFECTED:
            return

        try:
            import shutil
            from datetime import datetime

            # Create quarantine directory
            quarantine_dir = Path(VirusScanConfig.QUARANTINE_DIR)
            quarantine_dir.mkdir(parents=True, exist_ok=True)

            # Generate quarantine filename
            original_name = Path(file_path).name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            quarantine_name = f'{timestamp}_{original_name}.quarantine'
            quarantine_path = quarantine_dir / quarantine_name

            # Move file
            shutil.move(file_path, quarantine_path)

            # Create metadata file
            metadata_path = quarantine_path.with_suffix('.metadata.txt')
            with open(metadata_path, 'w') as f:
                f.write(f'Original Path: {file_path}\n')
                f.write(f'Threat: {threat_name}\n')
                f.write(f'Quarantined: {timestamp}\n')

            logger.info(f'File quarantined: {quarantine_path}')

        except Exception as e:
            logger.error(f'Failed to quarantine file: {str(e)}')

    @staticmethod
    def scan_file(file_path: str, use_cache: bool = True) -> ScanResult:
        """
        Scan a file for viruses

        Args:
            file_path: Path to file to scan
            use_cache: Whether to use cached results

        Returns:
            ScanResult instance

        Example:
            result = VirusScanner.scan_file('/path/to/file.pdf')
            if result.is_infected:
                print(f'Threat detected: {result.threat_name}')
        """
        # Check file size
        file_size = Path(file_path).stat().st_size
        if file_size > VirusScanConfig.MAX_SCAN_SIZE:
            logger.warning(f'File too large to scan: {file_size} bytes')
            return ScanResult(
                is_clean=True,
                scanner='skipped (too large)',
                scan_duration=0.0
            )

        # Calculate file hash
        file_hash = VirusScanner.get_file_hash(file_path)

        # Check cache
        if use_cache:
            cached_result = VirusScanner.get_cached_result(file_hash)
            if cached_result:
                logger.debug(f'Using cached scan result for {file_path}')
                return cached_result

        # Perform scan based on configuration
        scanner_type = VirusScanConfig.SCANNER_TYPE

        if scanner_type == 'disabled':
            logger.warning('Virus scanning is disabled')
            return ScanResult(
                is_clean=True,
                scanner='disabled',
                scan_duration=0.0,
                file_hash=file_hash
            )

        elif scanner_type == 'clamav':
            result = ClamAVScanner.scan_file(file_path)

        elif scanner_type == 'azure_defender':
            result = AzureDefenderScanner.scan_file(file_path)

        else:
            logger.error(f'Unknown scanner type: {scanner_type}')
            return ScanResult(
                is_clean=True,
                scanner='unknown',
                scan_duration=0.0,
                file_hash=file_hash
            )

        # Set file hash
        result.file_hash = file_hash

        # Cache clean results
        if result.is_clean:
            VirusScanner.cache_result(file_hash, result)

        # Quarantine infected files
        if result.is_infected:
            VirusScanner.quarantine_file(file_path, result.threat_name)

        return result

    @staticmethod
    def scan_upload(uploaded_file) -> ScanResult:
        """
        Scan an uploaded Django file

        Args:
            uploaded_file: Django UploadedFile instance

        Returns:
            ScanResult instance

        Example:
            def handle_upload(request):
                uploaded_file = request.FILES['file']
                result = VirusScanner.scan_upload(uploaded_file)

                if result.is_infected:
                    return JsonResponse({
                        'error': f'Virus detected: {result.threat_name}'
                    }, status=400)
        """
        import tempfile

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name

        try:
            # Scan temporary file
            result = VirusScanner.scan_file(temp_path)
            return result

        finally:
            # Clean up temporary file if not quarantined
            try:
                Path(temp_path).unlink()
            except FileNotFoundError:
                pass  # File was quarantined


# =============================================================================
# Django Integration
# =============================================================================

def validate_uploaded_file(uploaded_file):
    """
    Django validator for uploaded files

    Usage:
        from apps.security.virus_scanning import validate_uploaded_file

        class MyForm(forms.Form):
            file = forms.FileField(validators=[validate_uploaded_file])
    """
    from django.core.exceptions import ValidationError

    result = VirusScanner.scan_upload(uploaded_file)

    if result.is_infected:
        raise ValidationError(
            f'Virus detected: {result.threat_name}. The file has been quarantined.'
        )
