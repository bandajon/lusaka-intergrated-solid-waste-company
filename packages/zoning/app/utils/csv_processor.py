import pandas as pd
import numpy as np
from datetime import datetime
import hashlib
import os
from shapely.geometry import Polygon, Point, mapping
from sqlalchemy import func
from app import db
from app.models import Zone, CSVImport, ZoneTypeEnum, ZoneStatusEnum, ImportStatusEnum


class CSVProcessor:
    """Process CSV files to create zones"""
    
    # Lusaka approximate bounds
    LUSAKA_BOUNDS = {
        'min_lon': 27.5,
        'max_lon': 29.0,
        'min_lat': -16.0,
        'max_lat': -14.5
    }
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def process_file(self, filepath, user_id, csv_format='simple', 
                    name_prefix='Zone', default_zone_type='residential'):
        """Process CSV file and create zones"""
        
        # Create import record
        import_record = CSVImport(
            filename=os.path.basename(filepath),
            file_path=filepath,
            file_size=os.path.getsize(filepath),
            file_hash=self._calculate_file_hash(filepath),
            uploaded_by=user_id,
            csv_format=csv_format,
            status=ImportStatusEnum.PROCESSING
        )
        db.session.add(import_record)
        db.session.commit()
        
        try:
            # Read CSV
            df = pd.read_csv(filepath)
            import_record.rows_total = len(df)
            
            # Validate columns
            valid, df_copy = self._validate_columns(df, csv_format)
            if not valid:
                import_record.status = ImportStatusEnum.FAILED
                import_record.error_log = '; '.join(self.errors)
                db.session.commit()
                return {'success': False, 'error': self.errors[0]}
            
            # Process based on format
            if csv_format == 'simple':
                zones_created = self._process_simple_format(
                    df_copy, import_record, user_id, name_prefix, default_zone_type
                )
            elif csv_format == 'with_metadata':
                zones_created = self._process_metadata_format(
                    df_copy, import_record, user_id
                )
            elif csv_format == 'multi_zone':
                zones_created = self._process_multi_zone_format(
                    df_copy, import_record, user_id
                )
            
            # Update import record
            import_record.zones_created = zones_created
            import_record.status = ImportStatusEnum.COMPLETED
            import_record.processed_at = datetime.utcnow()
            import_record.warnings = self.warnings if self.warnings else None
            
            db.session.commit()
            
            return {
                'success': True,
                'zones_created': zones_created,
                'warnings': self.warnings
            }
            
        except Exception as e:
            import_record.status = ImportStatusEnum.FAILED
            import_record.error_log = str(e)
            db.session.commit()
            return {'success': False, 'error': str(e)}
    
    def _validate_columns(self, df, csv_format):
        """Validate and normalize column names"""
        # Create a copy to avoid modifying the original
        df_copy = df.copy()
        
        # Define flexible column mappings
        longitude_variants = ['longitude', 'lon', 'lng', 'long', 'x']
        latitude_variants = ['latitude', 'lat', 'y']
        
        # Find and standardize longitude column
        lon_col = None
        for variant in longitude_variants:
            matching_cols = [col for col in df_copy.columns if col.lower().strip() == variant.lower()]
            if matching_cols:
                lon_col = matching_cols[0]
                break
        
        if not lon_col:
            self.errors.append(f"No longitude column found. Expected one of: {', '.join(longitude_variants)}")
            return False, df_copy
        
        # Find and standardize latitude column
        lat_col = None
        for variant in latitude_variants:
            matching_cols = [col for col in df_copy.columns if col.lower().strip() == variant.lower()]
            if matching_cols:
                lat_col = matching_cols[0]
                break
        
        if not lat_col:
            self.errors.append(f"No latitude column found. Expected one of: {', '.join(latitude_variants)}")
            return False, df_copy
        
        # Rename columns to standard names
        if lon_col != 'longitude':
            df_copy = df_copy.rename(columns={lon_col: 'longitude'})
            self.warnings.append(f"Mapped column '{lon_col}' to 'longitude'")
        
        if lat_col != 'latitude':
            df_copy = df_copy.rename(columns={lat_col: 'latitude'})
            self.warnings.append(f"Mapped column '{lat_col}' to 'latitude'")
        
        # Check for format-specific columns
        if csv_format == 'with_metadata':
            if 'zone_name' not in df_copy.columns:
                # Look for alternatives
                name_variants = ['name', 'zone_name', 'zone', 'area_name', 'region']
                name_col = None
                for variant in name_variants:
                    matching_cols = [col for col in df_copy.columns if col.lower().strip() == variant.lower()]
                    if matching_cols:
                        name_col = matching_cols[0]
                        break
                
                if name_col and name_col != 'zone_name':
                    df_copy = df_copy.rename(columns={name_col: 'zone_name'})
                    self.warnings.append(f"Mapped column '{name_col}' to 'zone_name'")
                else:
                    self.errors.append("Missing 'zone_name' column for metadata format")
                    return False, df_copy
        
        elif csv_format == 'multi_zone':
            if 'zone_id' not in df_copy.columns:
                # Look for alternatives
                id_variants = ['zone_id', 'id', 'zone', 'group', 'polygon_id']
                id_col = None
                for variant in id_variants:
                    matching_cols = [col for col in df_copy.columns if col.lower().strip() == variant.lower()]
                    if matching_cols:
                        id_col = matching_cols[0]
                        break
                
                if id_col and id_col != 'zone_id':
                    df_copy = df_copy.rename(columns={id_col: 'zone_id'})
                    self.warnings.append(f"Mapped column '{id_col}' to 'zone_id'")
                else:
                    self.errors.append("Missing 'zone_id' column for multi-zone format")
                    return False, df_copy
        
        return True, df_copy
    
    def _validate_coordinates(self, lon, lat):
        """Validate coordinate values"""
        if not (-180 <= lon <= 180):
            return False, "Invalid longitude"
        if not (-90 <= lat <= 90):
            return False, "Invalid latitude"
        
        # Check Lusaka bounds
        if not (self.LUSAKA_BOUNDS['min_lon'] <= lon <= self.LUSAKA_BOUNDS['max_lon']):
            self.warnings.append(f"Longitude {lon} outside Lusaka bounds")
        if not (self.LUSAKA_BOUNDS['min_lat'] <= lat <= self.LUSAKA_BOUNDS['max_lat']):
            self.warnings.append(f"Latitude {lat} outside Lusaka bounds")
        
        return True, None
    
    def _process_simple_format(self, df, import_record, user_id, name_prefix, default_zone_type):
        """Process simple lon/lat format - creates single zone from all points"""
        coordinates = []
        failed_rows = 0
        
        for idx, row in df.iterrows():
            try:
                lon = float(row['longitude'])
                lat = float(row['latitude'])
                valid, error = self._validate_coordinates(lon, lat)
                if not valid:
                    failed_rows += 1
                    self.warnings.append(f"Row {idx + 2}: {error} - lon: {lon}, lat: {lat}")
                    continue
                
                # Round coordinates to avoid floating point precision issues
                lon_rounded = round(lon, 8)
                lat_rounded = round(lat, 8)
                coordinates.append((lon_rounded, lat_rounded))
                
            except (ValueError, TypeError) as e:
                failed_rows += 1
                self.warnings.append(f"Row {idx + 2}: Invalid coordinate format - {str(e)}")
                continue
        
        if len(coordinates) < 3:
            self.errors.append(f"Need at least 3 valid coordinates to create a zone. Found {len(coordinates)} valid coordinates out of {len(df)} total rows.")
            return 0
        
        # Remove duplicate consecutive coordinates (except for intentional closing)
        clean_coordinates = []
        for i, coord in enumerate(coordinates):
            if i == 0 or coord != coordinates[i-1]:
                clean_coordinates.append(coord)
        
        coordinates = clean_coordinates
        
        # Auto-close polygon if not already closed
        if len(coordinates) >= 3:
            first_coord = coordinates[0]
            last_coord = coordinates[-1]
            
            # Check if polygon is already closed (with some tolerance for floating point)
            tolerance = 1e-8
            is_closed = (abs(first_coord[0] - last_coord[0]) < tolerance and 
                        abs(first_coord[1] - last_coord[1]) < tolerance)
            
            if not is_closed:
                coordinates.append(first_coord)
                self.warnings.append("Polygon was automatically closed by adding the first coordinate as the last point")
            else:
                self.warnings.append("Polygon was already properly closed")
        
        # Final validation
        if len(coordinates) < 4:  # Need at least 4 points for a closed polygon
            self.errors.append(f"Need at least 3 unique coordinates plus closing point to create a zone. Found {len(coordinates)-1} unique coordinates.")
            return 0
        
        # Create zone
        try:
            from shapely.ops import transform
            import pyproj
            
            polygon = Polygon(coordinates)
            
            if not polygon.is_valid:
                # Try to fix the polygon
                polygon = polygon.buffer(0)
                if not polygon.is_valid:
                    self.errors.append("Cannot create valid polygon from provided coordinates. Check coordinate order and ensure they form a proper polygon.")
                    return 0
                else:
                    self.warnings.append("Polygon geometry was automatically corrected")
            
            # Convert to UTM for accurate area calculation
            wgs84 = pyproj.CRS('EPSG:4326')  # WGS84
            utm35s = pyproj.CRS('EPSG:32735')  # UTM Zone 35S for Lusaka
            transformer = pyproj.Transformer.from_crs(wgs84, utm35s, always_xy=True)
            utm_polygon = transform(transformer.transform, polygon)
            
            area_sqm = utm_polygon.area
            perimeter_m = utm_polygon.length
            
            zone = Zone(
                name=f"{name_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                code=f"CSV_{import_record.id}",
                zone_type=ZoneTypeEnum(default_zone_type.upper()),
                status=ZoneStatusEnum.DRAFT,
                geometry=mapping(polygon),
                area_sqm=area_sqm,
                perimeter_m=perimeter_m,
                centroid=mapping(polygon.centroid),
                created_by=user_id,
                csv_import_id=import_record.id,
                import_source='csv',
                import_metadata={
                    'format': 'simple', 
                    'points': len(coordinates),
                    'unique_points': len(coordinates) - 1,  # Excluding closing point
                    'original_rows': len(df),
                    'failed_rows': failed_rows,
                    'auto_closed': not is_closed if 'is_closed' in locals() else False
                }
            )
            
            db.session.add(zone)
            db.session.commit()
            
            import_record.rows_processed = len(df) - failed_rows
            import_record.rows_failed = failed_rows
            
            # Add success info
            self.warnings.append(f"Successfully created zone with area: {area_sqm:.2f} sq meters ({area_sqm/1e6:.4f} sq km)")
            self.warnings.append(f"Zone perimeter: {perimeter_m:.2f} meters ({perimeter_m/1000:.2f} km)")
            
            return 1
            
        except Exception as e:
            self.errors.append(f"Error creating zone: {str(e)}")
            import traceback
            traceback.print_exc()
            return 0
    
    def _process_metadata_format(self, df, import_record, user_id):
        """Process CSV with metadata - groups by zone_name"""
        zones_created = 0
        
        # Group by zone_name
        for zone_name, group in df.groupby('zone_name'):
            coordinates = []
            
            # Extract zone metadata from first row
            first_row = group.iloc[0]
            zone_type = first_row.get('zone_type', 'residential')
            description = first_row.get('description', '')
            
            for idx, row in group.iterrows():
                try:
                    lon = float(row['longitude'])
                    lat = float(row['latitude'])
                    valid, error = self._validate_coordinates(lon, lat)
                    if valid:
                        # Round coordinates to avoid floating point precision issues
                        lon_rounded = round(lon, 8)
                        lat_rounded = round(lat, 8)
                        coordinates.append((lon_rounded, lat_rounded))
                    else:
                        self.warnings.append(f"Zone '{zone_name}' Row {idx + 2}: {error}")
                except (ValueError, TypeError) as e:
                    self.warnings.append(f"Zone '{zone_name}' Row {idx + 2}: Invalid coordinate format - {str(e)}")
            
            if len(coordinates) < 3:
                self.warnings.append(f"Zone '{zone_name}' has less than 3 valid coordinates, skipping")
                continue
            
            # Remove duplicate consecutive coordinates
            clean_coordinates = []
            for i, coord in enumerate(coordinates):
                if i == 0 or coord != coordinates[i-1]:
                    clean_coordinates.append(coord)
            
            coordinates = clean_coordinates
            
            # Auto-close polygon if not already closed
            if len(coordinates) >= 3:
                first_coord = coordinates[0]
                last_coord = coordinates[-1]
                
                # Check if polygon is already closed (with some tolerance for floating point)
                tolerance = 1e-8
                is_closed = (abs(first_coord[0] - last_coord[0]) < tolerance and 
                            abs(first_coord[1] - last_coord[1]) < tolerance)
                
                if not is_closed:
                    coordinates.append(first_coord)
                    self.warnings.append(f"Zone '{zone_name}' polygon was automatically closed")
            
            if len(coordinates) < 4:  # Need at least 4 points for a closed polygon
                self.warnings.append(f"Zone '{zone_name}' needs at least 3 unique coordinates plus closing point. Found {len(coordinates)-1} unique coordinates. Skipping.")
                continue
            
            try:
                from shapely.ops import transform
                import pyproj
                
                polygon = Polygon(coordinates)
                
                if not polygon.is_valid:
                    polygon = polygon.buffer(0)
                    if not polygon.is_valid:
                        self.warnings.append(f"Zone '{zone_name}' has invalid geometry, skipping")
                        continue
                    else:
                        self.warnings.append(f"Zone '{zone_name}' geometry was automatically corrected")
                
                # Convert to UTM for accurate area calculation
                wgs84 = pyproj.CRS('EPSG:4326')
                utm35s = pyproj.CRS('EPSG:32735')
                transformer = pyproj.Transformer.from_crs(wgs84, utm35s, always_xy=True)
                utm_polygon = transform(transformer.transform, polygon)
                
                area_sqm = utm_polygon.area
                perimeter_m = utm_polygon.length
                
                zone_code = f"CSV_{import_record.id}_{len(zone_name)}"
                
                zone = Zone(
                    name=zone_name,
                    code=zone_code[:50],  # Ensure code length limit
                    description=description,
                    zone_type=ZoneTypeEnum(zone_type.upper()),
                    status=ZoneStatusEnum.DRAFT,
                    geometry=mapping(polygon),
                    area_sqm=area_sqm,
                    perimeter_m=perimeter_m,
                    centroid=mapping(polygon.centroid),
                    created_by=user_id,
                    csv_import_id=import_record.id,
                    import_source='csv',
                    import_metadata={
                        'format': 'with_metadata',
                        'zone_name': zone_name,
                        'points': len(coordinates),
                        'unique_points': len(coordinates) - 1,
                        'auto_closed': not is_closed if 'is_closed' in locals() else False
                    }
                )
                
                db.session.add(zone)
                zones_created += 1
                
                self.warnings.append(f"Zone '{zone_name}': {area_sqm:.2f} sq meters ({area_sqm/1e6:.4f} sq km)")
                
            except Exception as e:
                self.warnings.append(f"Error creating zone '{zone_name}': {str(e)}")
                continue
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            self.errors.append(f"Database error: {str(e)}")
            return 0
        
        return zones_created
    
    def _process_multi_zone_format(self, df, import_record, user_id):
        """Process multiple zones in single CSV"""
        zones_created = 0
        
        # Group by zone_id
        for zone_id, group in df.groupby('zone_id'):
            coordinates = []
            
            # Extract metadata
            first_row = group.iloc[0]
            zone_name = first_row.get('zone_name', f'Zone_{zone_id}')
            zone_type = first_row.get('zone_type', 'residential')
            
            for idx, row in group.iterrows():
                valid, error = self._validate_coordinates(row['longitude'], row['latitude'])
                if valid:
                    coordinates.append((row['longitude'], row['latitude']))
            
            if len(coordinates) < 3:
                self.warnings.append(f"Zone ID '{zone_id}' has less than 3 valid coordinates, skipping")
                continue
            
            # Close polygon
            if coordinates[0] != coordinates[-1]:
                coordinates.append(coordinates[0])
            
            try:
                polygon = Polygon(coordinates)
                
                if not polygon.is_valid:
                    self.warnings.append(f"Zone ID '{zone_id}' has invalid geometry, skipping")
                    continue
                
                zone_code = f"{zone_name.upper().replace(' ', '_')}_{import_record.id}_{zone_id}"
                
                zone = Zone(
                    name=zone_name,
                    code=zone_code[:50],
                    zone_type=ZoneTypeEnum(zone_type.upper()),
                    status=ZoneStatusEnum.DRAFT,
                    geometry=mapping(polygon),
                    area_sqm=polygon.area,
                    perimeter_m=polygon.length,
                    centroid=mapping(polygon.centroid),
                    created_by=user_id,
                    csv_import_id=import_record.id,
                    import_source='csv',
                    import_metadata={
                        'format': 'multi_zone',
                        'original_zone_id': str(zone_id),
                        'points': len(coordinates)
                    }
                )
                
                db.session.add(zone)
                zones_created += 1
                
            except Exception as e:
                self.warnings.append(f"Error creating zone ID '{zone_id}': {str(e)}")
        
        db.session.commit()
        import_record.rows_processed = len(df)
        return zones_created
    
    def _calculate_file_hash(self, filepath):
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()