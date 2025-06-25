from datetime import datetime
from sqlalchemy import String, JSON
from app import db
import enum


class ZoneTypeEnum(enum.Enum):
    RESIDENTIAL = "RESIDENTIAL"
    COMMERCIAL = "COMMERCIAL"
    INDUSTRIAL = "INDUSTRIAL"
    INSTITUTIONAL = "INSTITUTIONAL"
    MIXED_USE = "MIXED_USE"
    GREEN_SPACE = "GREEN_SPACE"


class ZoneStatusEnum(enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class Zone(db.Model):
    """Zone model with spatial data support"""
    __tablename__ = 'zones'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    
    # Spatial data - store as JSON for SQLite
    geometry = db.Column(JSON)
    centroid = db.Column(JSON)
    
    area_sqm = db.Column(db.Float)
    perimeter_m = db.Column(db.Float)
    
    # Zone attributes
    zone_type = db.Column(db.Enum(ZoneTypeEnum), nullable=False)
    status = db.Column(db.Enum(ZoneStatusEnum), default=ZoneStatusEnum.DRAFT)
    parent_zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'))
    
    # CSV import tracking
    import_source = db.Column(db.String(50))  # 'manual', 'csv', 'api'
    import_metadata = db.Column(JSON)
    original_csv_data = db.Column(db.Text)
    csv_import_id = db.Column(db.Integer, db.ForeignKey('csv_imports.id'))
    
    # Waste management attributes
    estimated_population = db.Column(db.Integer)
    household_count = db.Column(db.Integer)
    business_count = db.Column(db.Integer)
    waste_generation_kg_day = db.Column(db.Float)
    collection_frequency_week = db.Column(db.Integer, default=2)
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('zoning_users.id'), nullable=False)
    modified_by = db.Column(db.Integer, db.ForeignKey('zoning_users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional attributes
    zone_metadata = db.Column(JSON)
    tags = db.Column(JSON)  # Store as JSON array
    
    # Relationships
    parent_zone = db.relationship('Zone', remote_side=[id], backref='child_zones')
    analyses = db.relationship('ZoneAnalysis', backref='zone', lazy='dynamic',
                             cascade='all, delete-orphan')
    csv_import = db.relationship('CSVImport', backref='zones')
    
    def __repr__(self):
        return f'<Zone {self.code}: {self.name}>'
    
    @property
    def geojson(self):
        """Return zone as GeoJSON feature"""
        return {
            'type': 'Feature',
            'properties': {
                'id': self.id,
                'name': self.name,
                'code': self.code,
                'zone_type': self.zone_type.value if self.zone_type else None,
                'status': self.status.value if self.status else None,
                'area_sqm': self.area_sqm,
                'population': self.estimated_population
            },
            'geometry': self.geometry
        }


class ZoneAnalysis(db.Model):
    """Store analysis results for zones"""
    __tablename__ = 'zone_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'), nullable=False)
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Population analysis
    population_density_per_sqkm = db.Column(db.Float)
    household_density_per_sqkm = db.Column(db.Float)
    
    # Waste generation analysis
    total_waste_generation_kg_day = db.Column(db.Float)
    residential_waste_kg_day = db.Column(db.Float)
    commercial_waste_kg_day = db.Column(db.Float)
    industrial_waste_kg_day = db.Column(db.Float)
    
    # Collection analysis
    collection_points_required = db.Column(db.Integer)
    collection_vehicles_required = db.Column(db.Integer)
    collection_staff_required = db.Column(db.Integer)
    optimal_route_distance_km = db.Column(db.Float)
    
    # Revenue projection
    projected_monthly_revenue = db.Column(db.Float)
    residential_revenue = db.Column(db.Float)
    commercial_revenue = db.Column(db.Float)
    industrial_revenue = db.Column(db.Float)
    
    # Earth Engine analysis results
    building_count = db.Column(db.Integer)
    vegetation_coverage_percent = db.Column(db.Float)
    impervious_surface_percent = db.Column(db.Float)
    land_use_classification = db.Column(JSON)
    
    # Analysis metadata
    analysis_parameters = db.Column(JSON)
    earth_engine_task_id = db.Column(db.String(100))
    processing_time_seconds = db.Column(db.Float)
    
    created_by = db.Column(db.Integer, db.ForeignKey('zoning_users.id'))
    
    def __repr__(self):
        return f'<ZoneAnalysis for Zone {self.zone_id} on {self.analysis_date}>'


class TemporaryZoneAnalysis(db.Model):
    """Store analysis results for zones being drawn (not yet saved)"""
    __tablename__ = 'temporary_zone_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False, index=True)  # Browser session ID
    geometry_hash = db.Column(db.String(64), nullable=False, index=True)  # Hash of the geometry
    
    # Store the full analysis result as JSON
    analysis_data = db.Column(JSON, nullable=False)
    
    # Quick access fields for common queries
    estimated_population = db.Column(db.Integer)
    total_waste_kg_day = db.Column(db.Float)
    area_sqkm = db.Column(db.Float)
    viability_score = db.Column(db.Float)
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('zoning_users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # Auto-cleanup old entries
    
    def __repr__(self):
        return f'<TemporaryZoneAnalysis {self.id} for session {self.session_id}>'
    
    @staticmethod
    def cleanup_expired():
        """Clean up expired temporary analyses"""
        expired = TemporaryZoneAnalysis.query.filter(
            TemporaryZoneAnalysis.expires_at < datetime.utcnow()
        ).all()
        for analysis in expired:
            db.session.delete(analysis)
        db.session.commit()
        return len(expired)