<?php the_post(); ?>
<?php  ?>

<?php
$land76_single_post_id = (int) get_the_ID();
$land76_claims_managed_runtime = function_exists('land76wp_claims_managed_service_hub_post')
    && land76wp_claims_managed_service_hub_post($land76_single_post_id);
if ($land76_claims_managed_runtime) {
    $land76_managed_contract = function_exists('land76wp_managed_page_contract')
        ? land76wp_managed_page_contract($land76_single_post_id)
        : null;
    if (!is_array($land76_managed_contract)
        || !in_array($land76_managed_contract['role'], array('child', 'article'), true)) {
        global $wp_query;
        $wp_query->set_404();
        status_header(404);
        nocache_headers();
        $land76_not_found_template = get_404_template();
        if ($land76_not_found_template) {
            include $land76_not_found_template;
        }
        return;
    }

    get_header('seo');
    if ($land76_managed_contract['role'] === 'article') {
        include get_template_directory() . '/inc/seoblogpost.php';
    } else {
        include get_template_directory() . '/inc/newservicepost.php';
    }
    get_footer();
    return;
}

if (in_category(72)) {
    get_header('seo');
    include get_template_directory() . '/inc/seoblogpost.php';
} else if (in_category(87) || in_category(88) || in_category(89) || in_category(90) || in_category(91) || in_category(92) || in_category(74)) {
    get_header('seo');
    include get_template_directory() . '/inc/newservicepost.php';
} else if (in_category(75)) {
    get_header('post');
    include get_template_directory() . '/inc/oldpost.php';
}
?>


<?php get_footer(); ?>
