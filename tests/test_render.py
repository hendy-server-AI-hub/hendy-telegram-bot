from app.config import Settings
from app.services.render import RenderService


def make_service():
    settings = Settings(bot_token="123456:abcdefghijk", telegram_admin_ids="12345")
    return RenderService(client=None, settings=settings)


def test_render_deploy_confirmation_is_single_use():
    service = make_service()
    token = service.create_deploy_confirmation("srv-example_123")
    assert service.consume_deploy_confirmation(token) == "srv-example_123"
    assert service.consume_deploy_confirmation(token) is None


def test_render_service_id_rejects_path_injection():
    service = make_service()
    try:
        service.create_deploy_confirmation("../other-service")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid service ID to be rejected")
