from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from issue.models import *
from issue.models import PermissionModel as PermModel


class ProjectMiddleware:
    """
    This middleware must be call after authentication middleware.
    """

    def process_view(self, request, view, view_args, view_kwargs):

        if view.__module__ != 'issue.views':
            return

        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "The project middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE_CLASSES setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the ProjectMiddleware class.")

        if request.user.is_authenticated() and request.user.is_staff:
            projects = Project.objects.all()
        else:
            query = Q(public=True)
            if request.user.is_authenticated():
                # access granted through a team
                teams = request.user.teams.values_list('name')
                query |= Q(permissions__grantee_type=PermModel.GRANTEE_TEAM,
                           permissions__grantee_name__in=teams)
                # access granted through a group
                groups = request.user.groups.values_list('name')
                query |= Q(permissions__grantee_type=PermModel.GRANTEE_GROUP,
                           permissions__grantee_name__in=groups)
                # access granted by specific permission
                query |= Q(permissions__grantee_type=PermModel.GRANTEE_USER,
                           permissions__grantee_name=request.user.username)
            projects = Project.objects.filter(query).distinct()

        request.projects = projects

        project = view_kwargs.get('project')

        if not project:
            return
        try:
            project = projects.get(name=project)
        except ObjectDoesNotExist:
            if request.user.is_authenticated():
                raise PermissionDenied()
            else:
                return login_required(view)(request, *view_args, **view_kwargs)

        view_kwargs['project'] = project
        request.project = project
