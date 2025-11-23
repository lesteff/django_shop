from rest_framework.permissions import BasePermission


class IsManager(BasePermission):
    """
    Доступ только из группы Manager
    """

    def has_permission(self,request,view):
        return request.user.groups.filter(name='manager').exists()

class IsClient(BasePermission):
    """
    Доступ только из группы Client
    """
    def has_permission(self,request,view):
        return request.user.groups.filter(name='client').exists()