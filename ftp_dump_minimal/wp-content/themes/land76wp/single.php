<?php the_post(); ?>
<?php  ?>

<?php
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
