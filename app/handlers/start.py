from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router(name="start")


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "<b>HENDY TELEGRAM CONTROL BOT</b>\n"
        "Đã xác thực quyền quản trị.\n\n"
        "<b>GitHub</b>: /gh_repos, /gh_repo, /gh_file, /gh_workflows, /gh_dispatch, /gh_issue\n"
        "<b>Render</b>: /render_services, /render_service, /render_deploy\n"
        "<b>AI</b>: /ask nội_dung\n"
        "<b>Server</b>: /server_status\n"
        "<b>Security</b>: /security\n"
        "Danh sách lệnh: /help"
    )


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(
        "<b>LỆNH QUẢN TRỊ</b>\n\n"
        "<code>/gh_repos</code> – Liệt kê tối đa 100 repository mới cập nhật\n"
        "<code>/gh_repo ten-repo</code> – Chi tiết repository\n"
        "<code>/gh_file ten-repo path/to/file [branch]</code> – Đọc file văn bản\n"
        "<code>/gh_workflows ten-repo</code> – Workflow GitHub Actions\n"
        "<code>/gh_dispatch ten-repo workflow.yml main</code> – Yêu cầu chạy workflow\n"
        "<code>/gh_issue ten-repo | tiêu đề | nội dung</code> – Tạo issue\n\n"
        "<code>/render_services</code> – Liệt kê Render services\n"
        "<code>/render_service SERVICE_ID</code> – Chi tiết service và deploy gần đây\n"
        "<code>/render_deploy SERVICE_ID</code> – Hiện nút xác nhận trước khi deploy\n\n"
        "<code>/ask câu hỏi</code> – Gửi yêu cầu tới OpenAI Responses API\n"
        "<code>/server_status</code> – Kiểm tra endpoint HTTPS được cấu hình\n"
        "<code>/security</code> – Báo cáo cấu hình bảo mật\n\n"
        "Không hỗ trợ chạy shell tùy ý, xóa repository hoặc lộ secret."
    )
