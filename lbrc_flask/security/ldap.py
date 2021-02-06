import ldap
import traceback
from flask import current_app


class Ldap():
    @staticmethod
    def _ldap_uri():
        return current_app.config['LDAP_URI']

    @staticmethod
    def _ldap_user():
        return current_app.config['LDAP_USER']

    @staticmethod
    def _ldap_password():
        return current_app.config['LDAP_PASSWORD']

    @staticmethod
    def is_enabled():
        return len((Ldap._ldap_uri() or '').strip()) > 0

    @staticmethod
    def search(username):
        result = None

        try:
            l = ldap.initialize(Ldap._ldap_uri())
            l.protocol_version = 3
            l.set_option(ldap.OPT_REFERRALS, 0)

            l.simple_bind_s(
                Ldap._ldap_user(),
                Ldap._ldap_password(),
            )

            search_result = l.search_s(
                'DC=xuhl-tr,DC=nhs,DC=uk',
                ldap.SCOPE_SUBTREE,
                'sAMAccountName={}'.format(username),
            )

            if isinstance(search_result[0][1], dict):
                user = search_result[0][1]
                result = {
                    'username': user['sAMAccountName'][0].decode("utf-8"),
                    'email': user['mail'][0].decode("utf-8"),
                    'name': user['name'][0].decode("utf-8"),
                    'surname': user['sn'][0].decode("utf-8"),
                    'given_name': user['givenName'][0].decode("utf-8"),
                }

        except ldap.LDAPError as e:
            print(traceback.format_exc())
            current_app.logger.error(traceback.format_exc())
        
        finally:
            return result

    @staticmethod
    def validate_password(username, password):
        l = ldap.initialize(Ldap._ldap_uri())
        l.protocol_version = 3
        l.set_option(ldap.OPT_REFERRALS, 0)

        try:
            l.simple_bind_s(username, password)
            return True

        except ldap.LDAPError as e:
            print(e)
            current_app.logger.error(e)
            return False
