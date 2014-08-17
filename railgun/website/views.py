#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/views.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import uuid

from flask import render_template, url_for, redirect, flash, request, g, \
    send_from_directory
from flask.ext.babel import lazy_gettext, get_locale, gettext as _
from flask.ext.login import login_user, logout_user, current_user, \
    login_required, fresh_login_required
from werkzeug.exceptions import NotFound

from .context import app, db
from .navibar import navigates, NaviItem, set_navibar_identity
from .forms import SignupForm, SigninForm, ProfileForm
from .credential import UserContext
from .userauth import authenticate, auth_providers
from .codelang import languages
from .models import User, Handin
from .hw import homeworks


@app.route('/')
def index():
    g.scripts.headScripts()
    # only logged user can see the homeworks
    if (current_user.is_authenticated()):
        pass
    return render_template('index.html')


@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    # If railgun does not allow new user signup, show 403 forbidden
    # TODO: beautify this page.
    if (not app.config['ALLOW_SIGNUP']):
        return _('Sign up is turned off.'), 403
    form = SignupForm()
    if (form.validate_on_submit()):
        # Construct user data object
        user = User()
        form.populate_obj(user)
        user.set_password(form.password.data)
        user.fill_i18n_from_request()
        try:
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('signin'))
        except Exception:
            app.logger.exception('Cannot create account %s' % user.name)
        flash(_("I'm sorry but we may have met some trouble. Please try "
                "again."))
    return render_template('signup.html', form=form)


@app.route('/signin/', methods=['GET', 'POST'])
def signin():
    form = SigninForm()
    next_url = request.args.get('next')
    if (form.validate_on_submit()):
        # Check whether the user exists
        user = authenticate(form.login.data, form.password.data)
        if (user):
            # Now we can login this user and redirect to index!
            login_user(UserContext(user), remember=form.remember.data)
            return redirect(next_url or url_for('index'))
        # Report username or password error
        flash(_('Incorrect username or password.'), 'danger')
    return render_template('signin.html', form=form, next=next_url)


@app.route('/reauthenticate/', methods=['GET', 'POST'])
def reauthenticate():
    # Re-authenticate form is just like signin but do not contain "remember"
    form = SigninForm()
    del form['remember']
    next_url = request.args.get('next')

    if (form.validate_on_submit()):
        # Check whether the user exists
        user = authenticate(form.login.data, form.password.data)
        if (user):
            # Now we can login this user and redirect to index!
            login_user(UserContext(user), remember=True)
            return redirect(next_url or url_for('index'))
        # Report username or password error
        flash(_('Incorrect username or password.'), 'danger')
    return render_template('signin.html', form=form, next=next_url)


@app.route('/signout/')
def signout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/profile/edit/', methods=['GET', 'POST'])
@fresh_login_required
def profile_edit():
    # Profile edit should use typeahead.js
    g.scripts.deps('typeahead.js')

    # Create the profile form.
    # Note that some fields cannot be edited in certain auth providers,
    # which should be stripped from from schema.
    form = ProfileForm(obj=current_user.dbo)
    if (current_user.provider):
        auth_providers.init_form(current_user.provider, form)

    if (form.validate_on_submit()):
        # Set password if passwd field exists
        if ('password' in form):
            pwd = form.password.data
            if (pwd):
                current_user.set_password(pwd)
            del form['password']
            del form['confirm']
        else:
            pwd = None

        # Copy values into current_user object
        form.populate_obj(current_user.dbo)

        # Commit to main database and auth provider
        try:
            if (current_user.provider):
                auth_providers.push(current_user.dbo, pwd)
            db.session.commit()
            flash(_('Profile saved.'), 'info')
        except Exception:
            app.logger.exception('Cannot update account %s' % current_user.name)
            flash(_("I'm sorry but we may have met some trouble. Please try "
                    "again."), 'warning')
        return redirect(url_for('profile_edit'))

    # Clear password & confirm here is ok.
    if ('password' in form):
        form.password.data = None
        form.confirm.data = None

    return render_template('profile_edit.html', locale_name=str(get_locale()),
                           form=form)


@app.route('/homework/<slug>/', methods=['GET', 'POST'])
@login_required
def homework(slug):
    # set the identity for navibar (so that current page will be activated)
    set_navibar_identity('homework.%s' % slug)
    # load requested homework instance
    hw = g.homeworks.get_by_slug(slug)
    if (not hw):
        raise NotFound()
    # generate multiple forms with different prefix
    hwlangs = hw.get_code_languages()
    forms = {
        k: languages[k].upload_form(hw) for k in hwlangs
    }
    # detect which form is used
    handin_lang = None
    if (request.method == 'POST' and 'handin_lang' in request.form):
        # check deadline
        next_ddl = hw.get_next_deadline()
        if (not next_ddl):
            flash(_('This homework is out of date! '
                    'You cannot upload your submission.'), 'danger')
            return redirect(url_for('homework', slug=slug))
        # we must record the current next_ddl. during the request processing,
        # such deadline may pass so that our program may fail later
        g.ddl_date = next_ddl[0]
        g.ddl_scale = next_ddl[1]
        handin_lang = request.form['handin_lang']
        # check the data integrity of uploaded data
        if (forms[handin_lang].validate_on_submit()):
            handid = uuid.uuid4().get_hex()
            try:
                languages[handin_lang].handle_upload(
                    handid, hw, handin_lang, forms[handin_lang]
                )
                flash(_('You submission is accepted, please wait for results.'),
                      'success')
            except Exception:
                app.logger.exception('Error when adding submission to run '
                                     'queue.')
                flash(_('Internal server error, please try again.'), 'danger')
            # homework page is too long, so redirect to handins page, to
            # let flashed message clearer
            return redirect(url_for('handins'))

    # if handin_lang not determine, choose the first lang
    if handin_lang is None:
        handin_lang = hwlangs[0]
    return render_template(
        'homework.html', hw=hw, forms=forms, active_lang=handin_lang,
        hwlangs=hwlangs
    )


@app.route('/hwpack/<slug>/<lang>.zip')
def hwpack(slug, lang):
    # NOTE: I suppose that there's no need to guard the homework archives
    #       by @login_required. regarding this, the packed archives can be
    #       served by nginx, not flask framework, which should be much
    #       faster to be responded.
    filename = '%(slug)s/%(lang)s.zip' % {'slug': slug, 'lang': lang}
    return send_from_directory(app.config['HOMEWORK_PACK_DIR'], filename)


@app.route('/handin/')
@login_required
def handins():
    # get pagination argument
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    try:
        perpage = int(request.args.get('perpage', 10))
    except ValueError:
        perpage = 10
    # query about all handins
    handins = Handin.query.filter(Handin.user_id == current_user.id)
    # filter out the handins for deleted homeworks
    if (app.config['IGNORE_HANDINS_OF_REMOVED_HW']):
        handins = handins.filter(Handin.hwid.in_(homeworks.get_uuid_list()))
    # Sort the handins
    handins = handins.order_by('-id')
    # build pagination object
    return render_template(
        'handins.html', the_page=handins.paginate(page, perpage)
    )


@app.route('/handin/<uuid>/')
@login_required
def handin_detail(uuid):
    # Query about the handin record
    handin = Handin.query.filter(Handin.user_id == current_user.id,
                                 Handin.uuid == uuid).one()

    # Get the homework
    hw = g.homeworks.get_by_uuid(handin.hwid)

    # render the handin
    return render_template('handin_detail.html', handin=handin, hw=hw)


# Register all pages into navibar
navigates.add_view(title=lazy_gettext('Home'), endpoint='index')
navigates.add(
    NaviItem(
        title=lazy_gettext('Homework'),
        url=None,
        identity='homework',
        # title of homework is affected by request.accept_languages
        # so we should build subitems until they are used
        subitems=lambda: [
            NaviItem(title=hw.info.name, url=url_for('homework', slug=hw.slug),
                     identity='homework.%s' % hw.slug)
            for hw in g.homeworks
        ]
    )
)
navigates.add_view(title=lazy_gettext('Submission'), endpoint='handins')
