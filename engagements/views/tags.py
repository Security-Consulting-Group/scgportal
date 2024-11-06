# engagements/views/tags.py

from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from ..models import Tag
from django.core.exceptions import PermissionDenied

class TagCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Tag
    fields = ['name', 'color']
    template_name = 'engagements/tags/tag_form.html'
    permission_required = 'engagements.add_tag'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'id': self.object.id,
                'name': self.object.name,
                'color': self.object.color
            })
        return reverse_lazy('engagements:tag-list')

class TagListView(LoginRequiredMixin, ListView):
    model = Tag
    template_name = 'engagements/tags/tag_list.html'
    context_object_name = 'tags'

class TagManagementView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Tag
    template_name = 'engagements/tags/tag_management.html'
    context_object_name = 'tags'
    permission_required = 'engagements.change_tag'