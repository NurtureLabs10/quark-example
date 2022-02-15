from datetime import datetime, date, timedelta
from django.utils import timezone
import pytz

class Date(object):

    @classmethod
    def to_string(cls, date_object):
        def suffix(d):
            return 'th' if 11 <= d <= 13 else\
                {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')

        if date_object:
            return date_object.strftime('{S} %B, %Y').\
                replace('{S}', str(date_object.day) + suffix(date_object.day))
        return ""

    @classmethod
    def get_date_from_string(cls, date_str):
        return datetime.strptime(date_str,
                                 '%Y-%m-%d').date()

    @classmethod
    def today(cls):
        """Get date for today."""
        return (cls.now()).date()

    @classmethod
    def get_datetime(cls, date_object):
        """Convert date to datetime."""
        return datetime.combine(
            date_object,
            datetime.min.time()).\
            replace(
            tzinfo=timezone.now().tzinfo)

    @classmethod
    def to_date(cls, date_input):
        """Convert datetime objects to date objects."""
        if isinstance(date_input, datetime):
            return date_input.date()
        return date_input

    @classmethod
    def is_lesser_than_today(cls, date_input_2):
        """Compare date_input_1 and Date.today()."""
        return cls.to_datetime(date_input_2) < cls.to_datetime(cls.today())

    @classmethod
    def is_greater_than(cls, date_input_1, date_input_2):
        """Compare date_input_1 and date_input_2."""
        return cls.to_datetime(date_input_1) > cls.to_datetime(date_input_2)

    @classmethod
    def to_datetime(cls, date_input):
        """Convert date objects to datetime objects."""
        if isinstance(date_input, date):
            date_input = datetime(date_input.year,
                                  date_input.month,
                                  date_input.day)
        return date_input

    @classmethod
    def now(cls):
        return timezone.localtime(timezone.now())

    @classmethod
    def current_unix_timestamp(cls):
        return cls.totimestamp(dt=cls.now())

    @classmethod
    def totimestamp(cls, dt, epoch=datetime(1970, 1, 1)):
        epoch = epoch.replace(tzinfo=dt.tzinfo)
        td = dt - epoch
        return (td.microseconds +
                (td.seconds + td.days * 86400) * 10**6) / 10**6

    @classmethod
    def unix_timestamp_to_string(cls, timestamp):
        if timestamp:
            return Date.to_string(datetime.fromtimestamp(timestamp))
        return ""

    @classmethod
    def add_days(cls, date_object, days):
        return date_object + timedelta(days=days)

    @classmethod
    def get_start_of_week(cls):
        """Get the date on this weeks Monday."""
        return cls.add_days(cls.today(), -cls.today().weekday())

    @classmethod
    def get_end_of_week(cls):
        """Get the date on next weeks Monday."""
        return cls.add_days(cls.get_start_of_week(), 7)

    @classmethod
    def get_datetime_from_unix_time(cls, unix_time):
        """Returning datetime from unix_time."""
        if unix_time:
            return datetime.fromtimestamp(unix_time).\
                replace(tzinfo=cls.now().tzinfo)
        return None
