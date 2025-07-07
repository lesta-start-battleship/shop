from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
	def has_permission(self, request, view):
		user = request.user
		return (
				getattr(user, 'is_authenticated', False) and
				getattr(user, 'role', None) == 'admin'
		)
