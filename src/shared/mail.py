from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import send_mail
from shared.handle_get import get_users_from_ext_user
from common.helper import get_preferences



def email(subject, message, recipient_list):
    #subject = 'Thank you for registering to our site'
    #message = ' it  means a world to us '
    email_from = settings.EMAIL_HOST_USER
    #recipient_list = ['receiver@gmail.com',]
    send_mail( subject, message, email_from, recipient_list)


class Email:

    @staticmethod
    def get_from_email_address(ext_user=None):
        #return user.email

        email = get_preferences('sender_email')
        return f"PortfolioManager <{email}>"
    
    @staticmethod
    def get_to_email_address(ext_user=None):
        to_email = list()
        for user in get_users_from_ext_user(ext_user):
            if user.email and user.email!='':
                to_email.append(user.email)
        return to_email

    @staticmethod
    def is_email_setup(ext_user=None):
        email_backend = get_preferences('email_backend')
        if not email_backend or email_backend =='':
            return False
        from_email = Email.get_from_email_address(ext_user)
        if not from_email or from_email == '':
            return False
        recipient_list = Email.get_to_email_address(ext_user)
        if not recipient_list or (type(recipient_list) == list and len(recipient_list)==0):
            print(f'not sending email because of empty recipient list')
            return False
        return True

    @staticmethod
    def send(subject, message, html_message, ext_user=None, recipient_list=None):
        from_email = Email.get_from_email_address(ext_user)
        if not from_email or from_email == '':
            print("not sending email since sender email is empty")
            return
        if not recipient_list:
            recipient_list = Email.get_to_email_address(ext_user)
        if not recipient_list or (type(recipient_list) == list and len(recipient_list)==0):
            print(f'not sending email because of empty recipient list')
            return
        email_backend = get_preferences('email_backend')
        if not email_backend or email_backend =='':
            return
        if email_backend == 'Mailjet':
            email_api_key = get_preferences('email_api_key')
            email_api_secret = get_preferences('email_api_secret')
            
            settings.ANYMAIL = {
                "MAILJET_API_KEY": email_api_key,
                "MAILJET_SECRET_KEY": email_api_secret,
            }
            if not email_api_key or email_api_key =='' or not email_api_secret or email_api_secret =='':
                print(f'not sending email because of empty email api key or secret')
                return
            settings.EMAIL_BACKEND = 'anymail.backends.mailjet.EmailBackend'
            settings.ANYMAIL = {
                "MAILJET_API_KEY": email_api_key,
                "MAILJET_SECRET_KEY": email_api_secret,
            }
            send_mail(subject=subject, message=message, from_email=from_email, recipient_list=recipient_list, html_message=html_message)
            print(f'email sent to {recipient_list}')
            return
        print(f'mail not sent')
