from datetime import datetime
from app import db
import enum
from sqlalchemy import JSON


class ImportStatusEnum(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class CSVImport(db.Model):
    """Track CSV imports and their status"""
    __tablename__ = 'csv_imports'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    file_hash = db.Column(db.String(64))  # SHA-256 hash for duplicate detection
    
    # Import details
    uploaded_by = db.Column(db.Integer, db.ForeignKey('zoning_users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # Processing statistics
    rows_total = db.Column(db.Integer)
    rows_processed = db.Column(db.Integer)
    rows_failed = db.Column(db.Integer)
    zones_created = db.Column(db.Integer, default=0)
    zones_updated = db.Column(db.Integer, default=0)
    
    # Status tracking
    status = db.Column(db.Enum(ImportStatusEnum), default=ImportStatusEnum.PENDING)
    error_log = db.Column(db.Text)
    warnings = db.Column(JSON)
    
    # Import configuration
    csv_format = db.Column(db.String(50))  # 'simple', 'with_metadata', 'multi_zone'
    column_mapping = db.Column(JSON)  # Maps CSV columns to zone attributes
    import_options = db.Column(JSON)  # Additional import settings
    
    # Validation results
    validation_errors = db.Column(JSON)
    coordinate_system = db.Column(db.String(20), default='WGS84')
    bounds_check_passed = db.Column(db.Boolean)
    
    # Processing metadata
    processing_time_seconds = db.Column(db.Float)
    memory_usage_mb = db.Column(db.Float)
    
    def __repr__(self):
        return f'<CSVImport {self.filename} by User {self.uploaded_by}>'
    
    @property
    def success_rate(self):
        """Calculate import success rate"""
        if self.rows_total and self.rows_total > 0:
            return ((self.rows_processed - self.rows_failed) / self.rows_total) * 100
        return 0
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'filename': self.original_filename,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'status': self.status.value if self.status else None,
            'rows_total': self.rows_total,
            'rows_processed': self.rows_processed,
            'zones_created': self.zones_created,
            'success_rate': self.success_rate,
            'errors': self.validation_errors,
            'warnings': self.warnings
        }