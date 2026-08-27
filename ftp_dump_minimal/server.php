<?php

/** Handle contact forms without reporting a false success to the browser. */

header('Content-Type: text/plain; charset=UTF-8');
header('Cache-Control: no-store');

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    header('Allow: POST');
    http_response_code(405);
    exit('Method not allowed');
}

function land76_clean_post_value($key, $max_length)
{
    $value = $_POST[$key] ?? '';
    if (!is_string($value)) {
        return '';
    }

    $value = trim(strip_tags($value));
    $value = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]+/u', ' ', $value);
    if ($value === null) {
        return '';
    }

    if (function_exists('mb_substr')) {
        return mb_substr($value, 0, $max_length, 'UTF-8');
    }

    return substr($value, 0, $max_length);
}

$recipient = 'info@exp76.ru';
$site_name = 'exp76.ru';
$name = land76_clean_post_value('name', 120);
$phone = land76_clean_post_value('phone', 64);
$email = land76_clean_post_value('email', 254);
$source = land76_clean_post_value('source', 512);
$form_version = land76_clean_post_value('form_version', 64);
$consent = $_POST['consent'] ?? '';
$phone_digits = preg_replace('/\D+/', '', $phone);

if ($name === '' || !is_string($phone_digits) || strlen($phone_digits) < 7) {
    http_response_code(422);
    exit('Name and valid phone are required');
}

if ($email !== '' && !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(422);
    exit('Invalid email');
}

if ($form_version !== '' && $consent !== '1') {
    http_response_code(422);
    exit('Consent is required');
}

if ($source !== '' && !preg_match('~^(?:https://exp76\.ru(?:/|$)|/)~i', $source)) {
    $source = '';
}

$message_lines = array(
    'Имя: ' . $name,
    'Телефон: ' . $phone,
);
if ($email !== '') {
    $message_lines[] = 'Email: ' . $email;
}
if ($source !== '') {
    $message_lines[] = 'Страница: ' . $source;
}
if ($form_version !== '') {
    $message_lines[] = 'Форма: ' . $form_version;
    $message_lines[] = 'Согласие: подтверждено';
    $message_lines[] = 'Дата согласия: ' . date(DATE_ATOM);
}

$message = implode("\n", $message_lines);
$subject_text = 'Новая заявка с сайта "' . $site_name . '"';
$subject = '=?UTF-8?B?' . base64_encode($subject_text) . '?=';
$headers = "Content-Type: text/plain; charset=UTF-8\r\nFrom: {$recipient}";
$mail_sent = @mail($recipient, $subject, $message, $headers);

if (!$mail_sent) {
    error_log('exp76.ru contact form: mail delivery was not accepted');
    http_response_code(500);
    exit('Unable to send request');
}

http_response_code(200);
exit('OK');
