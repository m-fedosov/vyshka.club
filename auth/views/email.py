import datetime
from datetime import date

import random

from django.conf import settings
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django_q.tasks import async_task

from auth.helpers import set_session_cookie
from auth.models import Session, Code
from notifications.email.users import send_auth_email
from notifications.telegram.users import notify_user_auth
from users.models.user import User


def email_auth(request):  # функция создания нового челика
    if request.method != "POST":
        return redirect("login")
    goto = request.POST.get("goto")
    email = request.POST.get("email")
    if not email:
        return redirect("login")
    email = email.strip()
    user = User.objects.filter(Q(email=email.lower()) | Q(slug=email)).first()
    if not user and ((email[-7:] == ".hse.ru") or (email[-7:] == "@hse.ru")):  # если чел ещё не зарегался и он из вышки, то создаём его профиль
        user = User()
        user.email = email.lower()
        user.slug = user.email[:user.email.index("@")] + str(random.randint(0, 1024))
        user.is_email_unsubscribed = True
        user.is_email_verified = False
        user.moderation_status = User.MODERATION_STATUS_INTRO
        user.full_name = user.email[:user.email.index("@")]
        user.avatar = None
        user.company = None
        user.position = None
        user.city = None
        user.country = None
        user.geo = None
        user.bio = None
        user.contact = None
        user.email_digest_type = User.EMAIL_DIGEST_TYPE_NOPE
        user.telegram_id = None
        user.telegram_data = None
        user.membership_platform_data = None
        user.membership_started_at = datetime.datetime.now()
        user.membership_expires_at = date.fromisoformat('3022-04-25')
        user.save()
        return render(request, "payments/messages/done.html", {
                "email": user.email,
                "goto": goto,
                "restore": user.deleted_at is not None,
            })
    elif user:  # такой пользователь уже есть
        return render(request, "error.html", {
                "title": "Такой пользователь уже зарегистрирован в клубе 🦩",
            "message":  "Почта, которая была введена на странице для <b>регистрастрации</b>, уже привязана к аккаунту клуба."
                        "<p></p>"
                        "Помни: одна почта вышки - один аккаунт"
                        "<p></p>"
                        "Для входа в этот аккаунт нужно ввести email на этой 👉 <a href='https://vyshka.club/auth/login/'>странице</a> 👈"
                        "<p></p>"
                        "Если тебе нужна помощь, напиши нам, попробуем помочь."
            }, status=404)
    else:  # пользователь ввёл не почту вышки
        return render(request, "error.html", {
                "title": "Извини 🔒",
            "message":  "Клуб - закрытое сообщество для студентов <a href='https://hse.ru'><b>Вышки ⚰</b></a>"
                        "<p></p>"
                        "Для регистрации в клубе введи <b>корпоративную почту ВШЭ</b>, например:"
                        "<ul><li>email@hse.ru</li>"
                        "<li>name@miem.hse.ru</li>"
                        "<li>nice@edu.hse.ru</li></ul>"
                        "<p></p>"
                        "Если тебе нужна помощь, напиши нам, попробуем помочь."
            }, status=404)


def email_login(request):  # функция авторизации пользователя
    if request.method != "POST":
        return redirect("login")

    goto = request.POST.get("goto")
    email_or_login = request.POST.get("email_or_login")
    if not email_or_login:
        return redirect("login")

    email_or_login = email_or_login.strip()

    if "|-" in email_or_login:
        # secret_hash login
        email_part, secret_hash_part = email_or_login.split("|-", 1)
        user = User.objects.filter(email=email_part, secret_hash=secret_hash_part).first()
        if not user:
            return render(request, "error.html", {
                "title": "Такого юзера нет 🤔",
                "message": "Пользователь с таким кодом не найден. "
                           "Попробуйте авторизоваться по вышкинской почте или юзернейму.",
            }, status=404)

        if user.deleted_at:
            # cancel user deletion
            user.deleted_at = None
            user.save()

        session = Session.create_for_user(user)
        redirect_to = reverse("profile", args=[user.slug]) if not goto else goto
        response = redirect(redirect_to)
        return set_session_cookie(response, user, session)
    else:
        # email/nickname login
        user = User.objects.filter(Q(email=email_or_login.lower()) | Q(slug=email_or_login)).first()
        if not user:
            return render(request, "error.html", {
                "title": "Кто ты такой 🦚",
                "message": "Пользователь с такой почтой не найден в списке членов Клуба."
                        "<ul><li>Попробуйте <b>вышкинскую</b> почту или никнейм(если ты уже состоишь в клубе): </li>"
                        " <ul><li>email@hse.ru</li>"
                        " <li>name@miem.hse.ru</li>"
                        " <li>nice@edu.hse.ru</li></ul>"
                        "<li>Если совсем ничего не выйдет, напишите нам, попробуем помочь.</li>"
                        "</ul>",
            }, status=404)

        code = Code.create_for_user(user=user, recipient=user.email, length=settings.AUTH_CODE_LENGTH)
        async_task(send_auth_email, user, code)
        async_task(notify_user_auth, user, code)

        return render(request, "auth/email.html", {
            "email": user.email,
            "goto": goto,
            "restore": user.deleted_at is not None,
        })


def email_login_code(request):
    email = request.GET.get("email")
    code = request.GET.get("code")
    if not email or not code:
        return redirect("login")

    goto = request.GET.get("goto")
    email = email.lower().strip()
    code = code.lower().strip()

    user = Code.check_code(recipient=email, code=code)
    session = Session.create_for_user(user)

    if not user.is_email_verified:
        # save 1 click and verify email
        user.is_email_verified = True
        user.save()

    if user.deleted_at:
        # cancel user deletion
        user.deleted_at = None
        user.save()

    redirect_to = reverse("profile", args=[user.slug]) if not goto else goto
    response = redirect(redirect_to)
    return set_session_cookie(response, user, session)
