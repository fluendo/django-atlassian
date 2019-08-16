from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.deprecation import MiddlewareMixin

import logging
import netaddr

logger = logging.getLogger(__name__)


class IpWhiteListMiddleware(MiddlewareMixin):
    """
    Middleware which just only allows requests from  ip address set in settings.py with variable name ALLOWED_IPS
    """

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ips = x_forwarded_for.split(',')
            ips = map(str.strip, ips)
        else:
            ips = [request.META.get('REMOTE_ADDR')]
        return ips

    def is_blocked_ip(self, request):
        blocked = True 
        ips = self.get_client_ip(request)
        for ip in ips:
            ip_req = netaddr.IPAddress(ip)
            if ip in settings.ALLOWED_IPS:
                blocked = None
                break
            for allowed_range in settings.ALLOWED_IP_RANGES:
                network = netaddr.IPNetwork(allowed_range)
                if ip_req in network:
                    blocked = None 
                    break
        return blocked

    def process_request(self, request):
        if settings.RESTRICT_IPS:
            blocked = self.is_blocked_ip(request)
            if blocked:
                logger.info('Ip not allowed') 
                raise PermissionDenied()
        return None