import pytz
from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, IntegerField, SelectMultipleField, SubmitField, HiddenField
)
from wtforms.validators import DataRequired, Optional, NumberRange
from wtforms.widgets import CheckboxInput, ListWidget
from croniter import croniter


COMMON_TIMEZONES = sorted(pytz.common_timezones)


class ScheduleForm(FlaskForm):
    frequency = SelectField(
        'Frequency',
        choices=[
            ('daily', 'Daily'),
            ('weekdays', 'Weekdays (Mon-Fri)'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('custom', 'Custom (cron expression)'),
        ],
        default='daily',
    )
    hour = IntegerField('Hour', default=9, validators=[NumberRange(min=0, max=23)])
    minute = IntegerField('Minute', default=0, validators=[NumberRange(min=0, max=59)])
    days_of_week = StringField('Days of Week', description='Comma-separated: 0=Mon,...,6=Sun')
    day_of_month = IntegerField('Day of Month', default=1, validators=[Optional(), NumberRange(min=1, max=31)])
    cron_expression = StringField('Cron Expression', validators=[Optional()])
    timezone = SelectField('Timezone', choices=[(tz, tz) for tz in COMMON_TIMEZONES], default='UTC')
    submit = SubmitField('Save Schedule')

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False

        # Build or validate cron expression
        freq = self.frequency.data
        h = self.hour.data or 0
        m = self.minute.data or 0

        if freq == 'daily':
            self.cron_expression.data = f'{m} {h} * * *'
        elif freq == 'weekdays':
            self.cron_expression.data = f'{m} {h} * * 1-5'
        elif freq == 'weekly':
            days = self.days_of_week.data or '1'
            self.cron_expression.data = f'{m} {h} * * {days}'
        elif freq == 'monthly':
            dom = self.day_of_month.data or 1
            self.cron_expression.data = f'{m} {h} {dom} * *'
        elif freq == 'custom':
            if not self.cron_expression.data:
                self.cron_expression.errors.append('Cron expression is required for custom frequency.')
                return False

        # Validate the resulting cron expression
        try:
            croniter(self.cron_expression.data)
        except (ValueError, KeyError) as e:
            self.cron_expression.errors.append(f'Invalid cron expression: {e}')
            return False

        return True
