from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length


class MessageForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=255)])
    body = TextAreaField('Message Body', validators=[DataRequired()])
    response_type = SelectField(
        'Response Type',
        choices=[('yes_no', 'Yes / No'), ('custom', 'Custom Options')],
        default='yes_no',
    )
    custom_options_raw = StringField(
        'Custom Options',
        description='Comma-separated list, e.g. Good, OK, Bad',
    )
    submit = SubmitField('Save Message')
