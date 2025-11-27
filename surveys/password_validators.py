from django.core.exceptions import ValidationError
from django.utils.translation import ngettext


class EmployeePasswordValidator:
    """
    Custom password validator that requires minimum 4 characters for all passwords.
    """
    
    def __init__(self, min_length=4):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                self.get_error_message(),
                code='password_too_short',
                params={'min_length': self.min_length},
            )

    def get_error_message(self):
        return (
            ngettext(
                "Пароль слишком короткий. Он должен содержать как минимум %d символ.",
                "Пароль слишком короткий. Он должен содержать как минимум %d символа.",
                self.min_length,
            )
            % self.min_length
        )

    def get_help_text(self):
        return ngettext(
            "Ваш пароль должен содержать как минимум %(min_length)d символ.",
            "Ваш пароль должен содержать как минимум %(min_length)d символа.",
            self.min_length,
        ) % {"min_length": self.min_length}