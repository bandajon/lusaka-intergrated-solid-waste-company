from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, IntegerField, FloatField, SubmitField, HiddenField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
from app.models import Zone, ZoneTypeEnum, ZoneStatusEnum


class ZoneForm(FlaskForm):
    """Form for creating/editing zones"""
    name = StringField('Zone Name', validators=[
        DataRequired(),
        Length(min=3, max=120)
    ])
    code = StringField('Zone Code', validators=[
        DataRequired(),
        Length(min=2, max=50)
    ])
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=500)
    ])
    zone_type = SelectField('Zone Type', choices=[
        (ZoneTypeEnum.RESIDENTIAL.value, 'Residential'),
        (ZoneTypeEnum.COMMERCIAL.value, 'Commercial'),
        (ZoneTypeEnum.INDUSTRIAL.value, 'Industrial'),
        (ZoneTypeEnum.INSTITUTIONAL.value, 'Institutional'),
        (ZoneTypeEnum.MIXED_USE.value, 'Mixed Use'),
        (ZoneTypeEnum.GREEN_SPACE.value, 'Green Space')
    ], validators=[DataRequired()])
    
    status = SelectField('Status', choices=[
        (ZoneStatusEnum.DRAFT.value, 'Draft'),
        (ZoneStatusEnum.ACTIVE.value, 'Active'),
        (ZoneStatusEnum.INACTIVE.value, 'Inactive')
    ], default=ZoneStatusEnum.DRAFT.value)
    
    # Demographics
    estimated_population = IntegerField('Estimated Population', validators=[
        Optional(),
        NumberRange(min=0)
    ])
    household_count = IntegerField('Household Count', validators=[
        Optional(),
        NumberRange(min=0)
    ])
    business_count = IntegerField('Business Count', validators=[
        Optional(),
        NumberRange(min=0)
    ])
    
    # Collection settings
    collection_frequency_week = IntegerField('Collection Frequency (per week)', validators=[
        Optional(),
        NumberRange(min=1, max=7)
    ], default=2)
    
    # Area configuration fields
    settlement_density = SelectField('Settlement Density', choices=[
        ('high_density', 'High Density (>100 people/hectare)'),
        ('medium_density', 'Medium Density (50-100 people/hectare)'),
        ('low_density', 'Low Density (<50 people/hectare)'),
        ('informal_settlement', 'Informal Settlement')
    ], validators=[DataRequired()], default='medium_density')
    
    average_household_charge = FloatField('Average Household Charge (K/month)', validators=[
        DataRequired(),
        NumberRange(min=0, max=2000)
    ], default=150, description='Average amount charged per household per month')
    
    waste_generation_rate = FloatField('Waste Generation Rate (kg/person/day)', validators=[
        Optional(),
        NumberRange(min=0.1, max=5.0)
    ], default=0.5, description='Leave blank to use default rates by area type')
    
    socioeconomic_level = SelectField('Socioeconomic Level', choices=[
        ('low_income', 'Low Income (K500-2000/month)'),
        ('middle_income', 'Middle Income (K2000-8000/month)'),
        ('high_income', 'High Income (K8000+/month)'),
        ('mixed_income', 'Mixed Income')
    ], validators=[DataRequired()], default='mixed_income')
    
    # Hidden field for geometry
    geometry = HiddenField('Geometry')
    
    submit = SubmitField('Save Zone')
    
    def validate_code(self, field):
        """Ensure zone code is unique"""
        try:
            query = Zone.query.filter_by(code=field.data)
            # When editing, exclude the current zone from uniqueness check
            if hasattr(self, '_obj') and self._obj and hasattr(self._obj, 'id'):
                query = query.filter(Zone.id != self._obj.id)
            
            existing_zone = query.first()
            if existing_zone:
                raise ValidationError('Zone code already exists. Please choose another.')
        except Exception as e:
            print(f"Error in zone code validation: {str(e)}")
            # Don't raise validation error for database issues
            pass


class CSVUploadForm(FlaskForm):
    """Form for CSV upload"""
    csv_file = FileField('CSV File', validators=[
        FileRequired(),
        FileAllowed(['csv', 'txt'], 'Only CSV files are allowed!')
    ])
    
    csv_format = SelectField('CSV Format', choices=[
        ('simple', 'Simple (lon, lat)'),
        ('with_metadata', 'With Metadata (lon, lat, name, type, etc.)'),
        ('multi_zone', 'Multiple Zones (zone_id, lon, lat, ...)')
    ], default='simple', validators=[DataRequired()])
    
    name_prefix = StringField('Zone Name Prefix', validators=[
        Optional(),
        Length(max=50)
    ], description='Prefix for auto-generated zone names')
    
    default_zone_type = SelectField('Default Zone Type', choices=[
        (ZoneTypeEnum.RESIDENTIAL.value, 'Residential'),
        (ZoneTypeEnum.COMMERCIAL.value, 'Commercial'),
        (ZoneTypeEnum.INDUSTRIAL.value, 'Industrial'),
        (ZoneTypeEnum.INSTITUTIONAL.value, 'Institutional'),
        (ZoneTypeEnum.MIXED_USE.value, 'Mixed Use'),
        (ZoneTypeEnum.GREEN_SPACE.value, 'Green Space')
    ], default=ZoneTypeEnum.RESIDENTIAL.value,
    description='Default type for zones without type specification')
    
    validate_coordinates = BooleanField('Validate Coordinates', default=True,
                                      description='Check if coordinates are within Lusaka bounds')
    
    create_as_draft = BooleanField('Create as Draft', default=True,
                                  description='Create zones in draft status for review')
    
    submit = SubmitField('Upload and Process')