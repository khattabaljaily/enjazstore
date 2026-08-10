from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Any staff account can use the dashboard's day-to-day tools."""

    login_url = 'accounts:login'

    def test_func(self):
        return self.request.user.is_staff


class ManagerRequiredMixin(StaffRequiredMixin):
    """Employees and reports are manager-only — staff shouldn't manage each other."""

    def test_func(self):
        return super().test_func() and self.request.user.is_manager


class SuperuserRequiredMixin(StaffRequiredMixin):
    """Destructive actions (deleting records, cancelling orders) are superuser-only —
    regular staff and managers can't lose data or void a sale on their own."""

    def test_func(self):
        return super().test_func() and self.request.user.is_superuser
