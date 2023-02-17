from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed

from wtforms import StringField, PasswordField, BooleanField, SubmitField, FileField
from wtforms.validators import DataRequired
from wtforms.validators import ValidationError

def FileSizeLimit(max_size_in_mb):
    max_bytes = max_size_in_mb*1024*1024
    def file_length_check(form, field):
        if len(field.data.read()) > max_bytes:
            raise ValidationError(f"File size must be less than {max_size_in_mb}MB")
        field.data.seek(0)
    return file_length_check

class Upload_data(FlaskForm):
    bamfile = StringField('Setting 1', validators=[DataRequired()], default='be happy')
    uploaded_file = FileField('Input reference file', [FileRequired(), FileSizeLimit(max_size_in_mb=400)])

    submit = SubmitField('Upload all data')


class Upload_setting(FlaskForm):
    setting_1 = StringField('Setting 1', validators=[DataRequired()], default='be happy')
    setting_2 = StringField('Setting 2', validators=[DataRequired()], default='alpha')

    submit = SubmitField('Run analysis')