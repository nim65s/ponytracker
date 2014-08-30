from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser
from django.contrib import auth
from django.utils.encoding import python_2_unicode_compatible


__all__ = [ 'User', 'Group', 'Team' ]


@python_2_unicode_compatible
class User(AbstractUser):

    class Meta:
        ordering = [ 'username' ]

    @property
    def teams(self):
        query = Q(groups__in=self.groups.all()) | Q(users=self)
        return Team.objects.filter(query).distinct()

    @property
    def username_and_fullname(self):
        fullname = self.fullname
        if fullname:
            return "%s (%s)" % (self.username, fullname)
        else:
            return self.username

    @property
    def fullname(self):
        fullname = ''
        if self.first_name:
            fullname += self.first_name
        if self.last_name:
            if fullname:
                fullname += ' '
            fullname += self.last_name
        return fullname

    def __str__(self):
        return self.username


class Group(auth.models.Group):

    class Meta:
        ordering = [ 'name' ]
        proxy = True

    @property
    def users(self):
        return User.objects.filter(groups=self)


@python_2_unicode_compatible
class Team(models.Model):

    class Meta:
        ordering = [ 'name' ]

    name = models.CharField(max_length=128, unique=True)

    # We dont want related field on User object because we use
    # a special function that retrieve also team through group
    users = models.ManyToManyField(User, blank=True, null=True,
            related_name='+')
    groups = models.ManyToManyField(Group, blank=True, null=True,
            related_name='teams')

    def __str__(self):
        return self.name
