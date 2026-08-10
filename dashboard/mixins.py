from django.contrib import messages
from django.db.models import ProtectedError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render


def is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


class AjaxFormMixin:
    """Serves a bare form partial to a modal on GET, and JSON on POST.

    Falls back to the normal full-page CreateView/UpdateView behaviour
    when the request isn't AJAX, so the same URL works with JS disabled.
    """

    partial_template_name = None

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if is_ajax(request):
            return render(request, self.partial_template_name, self.get_context_data())
        return response

    def form_invalid(self, form):
        if is_ajax(self.request):
            return render(self.request, self.partial_template_name, self.get_context_data(form=form), status=400)
        return super().form_invalid(form)

    def form_valid(self, form):
        response = super().form_valid(form)
        if is_ajax(self.request):
            return JsonResponse({'success': True})
        return response


class AjaxDeleteMixin:
    """Deletes on POST and reports back as JSON for the confirm modal.

    Fully replaces DeleteView.post() (rather than calling super()) so the
    object is only ever fetched and deleted once.
    """

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        object_repr = str(self.object)
        try:
            self.object.delete()
        except ProtectedError:
            if is_ajax(request):
                return JsonResponse(
                    {'success': False, 'error': f'Can\'t delete "{object_repr}" — it\'s still in use.'},
                    status=400,
                )
            raise
        messages.success(request, f'"{object_repr}" deleted.')
        if is_ajax(request):
            return JsonResponse({'success': True})
        return HttpResponseRedirect(success_url)
