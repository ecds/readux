from ..utils import get_user_by_username_or_email

class UserSwitchMiddleware(object):
    def process_request(self, request):
        """ Switch User (su) """

        try:
            username = request.session['switched_username']
            user = get_user_by_username_or_email(username)
            if user:
                request.user = user
        except:
            pass



