<?php

/** Handle public contact forms through WordPress' validated mail pipeline. */

header('Content-Type: application/json; charset=UTF-8');
header('Cache-Control: no-store');

if (!is_readable(__DIR__ . '/wp-load.php')) {
    http_response_code(500);
    echo json_encode(array(
        'success' => false,
        'data' => array('code' => 'wordpress_unavailable'),
    ));
    exit;
}

require_once __DIR__ . '/wp-load.php';

function land76_contact_error($code, $message, $status)
{
    wp_send_json_error(array(
        'code' => $code,
        'message' => $message,
    ), $status);
}

function land76_contact_post_text($key, $max_length)
{
    $value = isset($_POST[$key]) ? wp_unslash($_POST[$key]) : '';
    if (!is_string($value)) {
        return '';
    }

    $value = sanitize_text_field($value);
    if (function_exists('mb_substr')) {
        return mb_substr($value, 0, $max_length, 'UTF-8');
    }

    return substr($value, 0, $max_length);
}

/** Return a non-reversible client identifier without trusting proxy headers. */
function land76_contact_client_hash()
{
    $remote_addr = isset($_SERVER['REMOTE_ADDR']) && is_string($_SERVER['REMOTE_ADDR'])
        ? trim($_SERVER['REMOTE_ADDR'])
        : '';
    if (filter_var($remote_addr, FILTER_VALIDATE_IP) === false) {
        $remote_addr = 'unknown';
    }

    return hash_hmac('sha256', $remote_addr, wp_salt('nonce'));
}

/** Build a bounded transient key whose material never exposes an IP or lead data. */
function land76_contact_throttle_key($scope, $material)
{
    $digest = hash_hmac('sha256', (string) $material, wp_salt('nonce'));

    return 'land76_contact_' . $scope . '_' . substr($digest, 0, 40);
}

/** Release only the replay lock acquired by this request. */
function land76_contact_release_replay_lock($lock_key, $lock_token)
{
    $lock = get_option($lock_key, array());
    if (is_array($lock)
        && isset($lock['token'])
        && is_string($lock['token'])
        && hash_equals($lock_token, $lock['token'])) {
        delete_option($lock_key);
    }
}

/** Atomically serialize access to one hashed throttle state key. */
function land76_contact_acquire_throttle_lock($state_key, $error_code, $error_message)
{
    $lock_key = land76_contact_throttle_key('lock', $state_key);
    $lock_token = wp_generate_uuid4();
    $lock = array(
        'token' => $lock_token,
        'expires' => time() + (2 * MINUTE_IN_SECONDS),
    );
    $acquired = add_option($lock_key, $lock, '', false);

    if (!$acquired) {
        $existing = get_option($lock_key, array());
        if (is_array($existing)
            && isset($existing['expires'])
            && (int) $existing['expires'] <= time()) {
            delete_option($lock_key);
            $acquired = add_option($lock_key, $lock, '', false);
        }
    }

    if (!$acquired) {
        land76_contact_error(
            $error_code,
            $error_message,
            429
        );
    }

    register_shutdown_function(
        'land76_contact_release_replay_lock',
        $lock_key,
        $lock_token
    );
}

/** Atomically serialize matching submissions before transient replay checks. */
function land76_contact_acquire_replay_lock($replay_key)
{
    land76_contact_acquire_throttle_lock(
        $replay_key,
        'duplicate_submission',
        'Такая заявка уже обрабатывается. Подождите немного перед повтором.'
    );
}

/** Reserve one validated submission and reject excessive or duplicate requests. */
function land76_contact_enforce_throttle($submission_fingerprint)
{
    $client_hash = land76_contact_client_hash();
    $replay_key = land76_contact_throttle_key('replay', $client_hash . ':' . $submission_fingerprint);
    land76_contact_acquire_replay_lock($replay_key);
    if (get_transient($replay_key) !== false) {
        land76_contact_error(
            'duplicate_submission',
            'Такая заявка уже отправлена. Подождите немного перед повтором.',
            429
        );
    }

    $rate_key = land76_contact_throttle_key('rate', $client_hash);
    land76_contact_acquire_throttle_lock($rate_key,
        'rate_limited',
        'Другая заявка уже обрабатывается. Попробуйте снова через минуту.'
    );
    $rate_count = get_transient($rate_key);
    $rate_count = $rate_count === false ? 0 : (int) $rate_count;
    if ($rate_count >= 5) {
        land76_contact_error(
            'rate_limited',
            'Слишком много заявок. Попробуйте снова через несколько минут.',
            429
        );
    }

    set_transient($rate_key, $rate_count + 1, 5 * MINUTE_IN_SECONDS);
    set_transient($replay_key, 1, 2 * MINUTE_IN_SECONDS);

    return $replay_key;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    header('Allow: POST');
    http_response_code(405);
    land76_contact_error('method_not_allowed', 'Отправьте форму методом POST.', 405);
}

$nonce = land76_contact_post_text('land76_nonce', 128);
if ($nonce === '' || !wp_verify_nonce($nonce, 'land76_contact_form')) {
    land76_contact_error('invalid_nonce', 'Сессия формы истекла. Обновите страницу.', 403);
}

if (land76_contact_post_text('website', 200) !== '') {
    land76_contact_error('spam_detected', 'Заявка отклонена.', 422);
}

$consent = isset($_POST['consent']) ? wp_unslash($_POST['consent']) : '';
if (!is_string($consent) || $consent !== '1') {
    land76_contact_error('consent_required', 'Подтвердите согласие на обработку данных.', 422);
}

$name = land76_contact_post_text('name', 120);
$phone = land76_contact_post_text('phone', 64);
$email = land76_contact_post_text('email', 254);
$source = land76_contact_post_text('source', 512);
$form_version = land76_contact_post_text('form_version', 64);
$phone_digits = preg_replace('/\D+/', '', $phone);

if ($name === '') {
    land76_contact_error('name_required', 'Укажите имя.', 422);
}

if (!is_string($phone_digits) || strlen($phone_digits) < 10 || strlen($phone_digits) > 15) {
    land76_contact_error('invalid_phone', 'Укажите корректный номер телефона.', 422);
}

if ($email !== '' && !is_email($email)) {
    land76_contact_error('invalid_email', 'Укажите корректный email.', 422);
}

$site_host = wp_parse_url(home_url('/'), PHP_URL_HOST);
$source_host = $source !== '' ? wp_parse_url($source, PHP_URL_HOST) : '';
$is_relative_source = strpos($source, '/') === 0 && strpos($source, '//') !== 0;
if ($source !== ''
    && !$is_relative_source
    && ($source_host === '' || strcasecmp((string) $source_host, (string) $site_host) !== 0)) {
    $source = '';
}

$message_lines = array(
    'Имя: ' . $name,
    'Телефон: ' . $phone,
    'Согласие: подтверждено',
    'Дата согласия: ' . current_time(DATE_ATOM),
);
if ($email !== '') {
    $message_lines[] = 'Email: ' . $email;
}
if ($source !== '') {
    $message_lines[] = 'Страница: ' . $source;
}
if ($form_version !== '') {
    $message_lines[] = 'Форма: ' . $form_version;
}

$submission_fingerprint = hash_hmac(
    'sha256',
    implode("\n", array($name, $phone_digits, $email, $source, $form_version)),
    wp_salt('nonce')
);
$replay_key = land76_contact_enforce_throttle($submission_fingerprint);

$recipient = apply_filters('land76_contact_recipient', 'info@exp76.ru');
$subject = 'Новая заявка с сайта exp76.ru';
$headers = array('Content-Type: text/plain; charset=UTF-8');
$mail_sent = wp_mail($recipient, $subject, implode("\n", $message_lines), $headers);

if (!$mail_sent) {
    delete_transient($replay_key);
    error_log('exp76.ru contact form: wp_mail rejected the message');
    wp_send_json_error(array(
        'code' => 'mail_failed',
        'message' => 'Не удалось отправить заявку. Позвоните нам или попробуйте позже.',
    ), 500);
}

wp_send_json_success(array(
    'code' => 'accepted',
    'message' => 'Заявка отправлена.',
));
