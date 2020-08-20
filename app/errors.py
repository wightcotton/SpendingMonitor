from flask import render_template
from app import app
from app.info_request_interface import InfoRequestHandler
from flask_login import current_user, login_required
from werkzeug.exceptions import InternalServerError


@app.errorhandler(InternalServerError)
def handle_500(e):
    original = getattr(e, "original_exception", None)
    if original is None:
        # direct 500 error, such as abort(500)
        return render_template("errors/500.html"), 500

    if 'NaTType' in original.args[0]:
        return render_template("errors/bad_file_data.html")

    return render_template("errors/500_unhandled.html", e=original), e.code
