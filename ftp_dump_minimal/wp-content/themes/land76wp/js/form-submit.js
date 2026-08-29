(function (root, factory) {
  var client = factory();

  if (typeof module === 'object' && module.exports) {
    module.exports = client;
  }

  if (root) {
    root.land76FormClient = client;
  }
})(typeof window !== 'undefined' ? window : null, function () {
  'use strict';

  function classifyResponse(status, body) {
    var payload;

    try {
      payload = JSON.parse(body);
    } catch (error) {
      return { ok: false, payload: null };
    }

    return {
      ok: Boolean(status >= 200 && status < 300 && payload && payload.success === true),
      payload: payload,
    };
  }

  function findMessage(form) {
    var container = form.parentElement;
    return container ? container.querySelector('.ajaxMessage') : null;
  }

  function ensureInlineStatus(form) {
    var container = form.parentElement;
    var status = container ? container.querySelector('.land76-form-status') : null;

    if (status) {
      return status;
    }

    status = form.ownerDocument.createElement('p');
    status.className = 'land76-form-status';
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    form.insertAdjacentElement('afterend', status);
    return status;
  }

  function resultMessage(result) {
    var data = result && result.payload ? result.payload.data : null;
    if (data && typeof data.message === 'string' && data.message) {
      return data.message;
    }
    return result && result.ok
      ? 'Заявка отправлена.'
      : 'Не удалось отправить заявку. Попробуйте ещё раз или позвоните нам.';
  }

  function setResultState(form, success, messageText) {
    var message = findMessage(form);
    var successMessage = message ? message.querySelector('.ajaxMessage__success') : null;
    var errorMessage = message ? message.querySelector('.ajaxMessage__error') : null;

    if (!message) {
      var status = ensureInlineStatus(form);
      status.hidden = false;
      status.textContent = messageText || (success ? 'Заявка отправлена.' : 'Не удалось отправить заявку.');
      status.classList.toggle('land76-form-status--success', success);
      status.classList.toggle('land76-form-status--error', !success);
      return;
    }

    form.style.display = success ? 'none' : '';
    message.style.display = 'block';
    message.classList.add('open');

    if (successMessage) {
      successMessage.classList.toggle('open', success);
      successMessage.style.display = success ? '' : 'none';
    }
    if (errorMessage) {
      errorMessage.classList.toggle('open', !success);
      errorMessage.style.display = success ? 'none' : '';
    }
  }

  function resetResultState(form) {
    var message = findMessage(form);
    var successMessage = message ? message.querySelector('.ajaxMessage__success') : null;
    var errorMessage = message ? message.querySelector('.ajaxMessage__error') : null;

    form.style.display = '';
    if (!message) {
      return;
    }

    message.classList.remove('open');
    message.style.display = 'none';
    if (successMessage) {
      successMessage.classList.remove('open');
      successMessage.style.display = '';
    }
    if (errorMessage) {
      errorMessage.classList.remove('open');
      errorMessage.style.display = '';
    }
  }

  function sendRequest(endpoint, formData, callback) {
    if (typeof window.fetch === 'function') {
      window
        .fetch(endpoint, {
          method: 'POST',
          body: formData,
          credentials: 'same-origin',
          headers: { Accept: 'application/json' },
        })
        .then(function (response) {
          return response.text().then(function (body) {
            callback(classifyResponse(response.status, body));
          });
        })
        .catch(function () {
          callback({ ok: false, payload: null });
        });
      return;
    }

    var request = new XMLHttpRequest();
    var completed = false;
    var finish = function (result) {
      if (completed) {
        return;
      }
      completed = true;
      callback(result);
    };
    request.open('POST', endpoint, true);
    request.setRequestHeader('Accept', 'application/json');
    request.onreadystatechange = function () {
      if (request.readyState === 4) {
        finish(classifyResponse(request.status, request.responseText));
      }
    };
    request.onerror = function () {
      finish({ ok: false, payload: null });
    };
    request.send(formData);
  }

  function submitForm(form) {
    var config = window.land76FormConfig || {};
    var nonceField = form.querySelector('[name="land76_nonce"]');
    var consent = form.querySelector('[name="consent"], .formConsent__input');
    var sourceField = form.querySelector('[name="source"]');
    var submit = form.querySelector('[type="submit"]');

    if (nonceField) {
      nonceField.value = config.nonce || '';
    }
    if (consent) {
      consent.name = 'consent';
      consent.value = '1';
    }
    if (sourceField) {
      sourceField.value = window.location.href;
    }

    var formData = new FormData(form);
    if (!nonceField) {
      formData.append('land76_nonce', config.nonce || '');
    }
    if (!consent || !consent.checked) {
      formData.append('consent', '');
    }
    if (!form.querySelector('[name="form_version"]')) {
      formData.append('form_version', 'site-form-v3');
    }
    if (!sourceField) {
      formData.append('source', window.location.href);
    }

    if (submit) {
      submit.disabled = true;
    }

    sendRequest(config.endpoint || '/server.php', formData, function (result) {
      setResultState(form, result.ok, resultMessage(result));
      if (result.ok) {
        form.reset();
      }
      if (submit) {
        submit.disabled = false;
      }
    });
  }

  function install() {
    if (typeof document === 'undefined' || document.documentElement.dataset.land76FormsReady) {
      return;
    }

    document.documentElement.dataset.land76FormsReady = '1';
    document.addEventListener(
      'submit',
      function (event) {
        var form = event.target;
        if (!form || !form.matches('.form')) {
          return;
        }

        event.preventDefault();
        event.stopImmediatePropagation();
        submitForm(form);
      },
      true
    );

    document.addEventListener('click', function (event) {
      var button = event.target.closest('.ajaxMessage__btn');
      var message = button ? button.closest('.ajaxMessage') : null;
      var wrapper = message ? message.parentElement : null;
      var form = wrapper ? wrapper.querySelector('.form') : null;
      if (form) {
        resetResultState(form);
      }
    });
  }

  if (typeof document !== 'undefined') {
    install();
  }

  return {
    classifyResponse: classifyResponse,
    install: install,
    resultMessage: resultMessage,
    setResultState: setResultState,
    submitForm: submitForm,
  };
});
