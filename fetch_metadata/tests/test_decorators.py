import inspect

from django.http import HttpResponse
from django.test import SimpleTestCase
from django.views import View

from fetch_metadata.decorators import fetch_metadata_exempt, fetch_metadata_policy


def _sync_view(request):
    """A sync view for testing."""
    return HttpResponse('ok')


async def _async_view(request):
    """An async view for testing."""
    return HttpResponse('ok')


class TestFetchMetadataExempt(SimpleTestCase):
    def test_sets_attribute_sync(self):
        # decorated sync view has fetch_metadata_exempt=True
        decorated = fetch_metadata_exempt(_sync_view)
        self.assertTrue(getattr(decorated, 'fetch_metadata_exempt', False))

    def test_sets_attribute_async(self):
        # decorated async view has fetch_metadata_exempt=True
        decorated = fetch_metadata_exempt(_async_view)
        self.assertTrue(getattr(decorated, 'fetch_metadata_exempt', False))

    def test_preserves_name(self):
        # @wraps preserves __name__
        decorated = fetch_metadata_exempt(_sync_view)
        self.assertEqual(decorated.__name__, '_sync_view')

    def test_preserves_docstring(self):
        # @wraps preserves __doc__
        decorated = fetch_metadata_exempt(_sync_view)
        self.assertEqual(decorated.__doc__, 'A sync view for testing.')

    def test_async_wrapper_is_coroutine(self):
        # async view gets async wrapper
        decorated = fetch_metadata_exempt(_async_view)
        self.assertTrue(inspect.iscoroutinefunction(decorated))

    def test_sync_wrapper_is_not_coroutine(self):
        # sync view gets sync wrapper
        decorated = fetch_metadata_exempt(_sync_view)
        self.assertFalse(inspect.iscoroutinefunction(decorated))

    def test_cbv_direct(self):
        # @fetch_metadata_exempt applied directly to a CBV
        @fetch_metadata_exempt
        class TestView(View):
            def get(self, request):
                return HttpResponse('ok')

        view_func = TestView.as_view()
        self.assertTrue(getattr(view_func, 'fetch_metadata_exempt', False))

    def test_cbv_subclass_inherits(self):
        # subclass of exempt CBV inherits the exemption
        @fetch_metadata_exempt
        class BaseView(View):
            def get(self, request):
                return HttpResponse('ok')

        class ChildView(BaseView):
            pass

        view_func = ChildView.as_view()
        self.assertTrue(getattr(view_func, 'fetch_metadata_exempt', False))

    def test_cbv_returns_class(self):
        # decorator returns the class itself, not a wrapper
        @fetch_metadata_exempt
        class TestView(View):
            def get(self, request):
                return HttpResponse('ok')

        self.assertTrue(inspect.isclass(TestView))
        self.assertTrue(issubclass(TestView, View))


class TestFetchMetadataPolicy(SimpleTestCase):
    def test_sets_policy_dict(self):
        # decorated view has fetch_metadata_policy dict with specified values
        decorated = fetch_metadata_policy(allowed_sites=['same-origin', 'same-site'])(_sync_view)
        policy = getattr(decorated, 'fetch_metadata_policy', None)
        self.assertIsNotNone(policy)
        self.assertEqual(policy['ALLOWED_SITES'], ['same-origin', 'same-site'])

    def test_partial_override(self):
        # only specified params appear in the policy dict
        decorated = fetch_metadata_policy(allow_navigations=False)(_sync_view)
        policy = getattr(decorated, 'fetch_metadata_policy', {})
        self.assertIn('ALLOW_NAVIGATIONS', policy)
        self.assertNotIn('ALLOWED_SITES', policy)
        self.assertNotIn('FAIL_OPEN', policy)

    def test_full_override(self):
        # all params specified
        decorated = fetch_metadata_policy(
            allowed_sites=['same-origin'],
            allow_navigations=False,
            fail_open=False,
        )(_sync_view)
        policy = getattr(decorated, 'fetch_metadata_policy', {})
        self.assertEqual(len(policy), 3)

    def test_preserves_name(self):
        decorated = fetch_metadata_policy(allowed_sites=['same-origin'])(_sync_view)
        self.assertEqual(decorated.__name__, '_sync_view')

    def test_async_support(self):
        # async view gets async wrapper
        decorated = fetch_metadata_policy(allowed_sites=['same-origin'])(_async_view)
        self.assertTrue(inspect.iscoroutinefunction(decorated))
        self.assertIsNotNone(getattr(decorated, 'fetch_metadata_policy', None))

    def test_cbv_direct(self):
        # @fetch_metadata_policy applied directly to a CBV
        @fetch_metadata_policy(allowed_sites=['same-origin', 'cross-site'])
        class TestView(View):
            def post(self, request):
                return HttpResponse('ok')

        view_func = TestView.as_view()
        policy = getattr(view_func, 'fetch_metadata_policy', None)
        self.assertIsNotNone(policy)
        self.assertIn('cross-site', policy['ALLOWED_SITES'])

    def test_cbv_subclass_inherits_policy(self):
        # subclass of policy-decorated CBV inherits the policy
        @fetch_metadata_policy(allowed_sites=['same-origin', 'same-site'])
        class BaseView(View):
            def get(self, request):
                return HttpResponse('ok')

        class ChildView(BaseView):
            pass

        view_func = ChildView.as_view()
        policy = getattr(view_func, 'fetch_metadata_policy', None)
        self.assertIsNotNone(policy)
        self.assertEqual(policy['ALLOWED_SITES'], ['same-origin', 'same-site'])

    def test_cbv_returns_class(self):
        # decorator returns the class itself, not a wrapper
        @fetch_metadata_policy(allowed_sites=['same-origin'])
        class TestView(View):
            def get(self, request):
                return HttpResponse('ok')

        self.assertTrue(inspect.isclass(TestView))
        self.assertTrue(issubclass(TestView, View))
