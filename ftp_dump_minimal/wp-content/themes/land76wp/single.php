<?php the_post(); ?>
<?php  ?>

<?php
if (in_category(87)) {
    get_header('seo');
    include get_template_directory() . '/inc/newservicepost.php';
} else if (in_category(72) || in_category(75)) {
    get_header('post');
    include get_template_directory() . '/inc/oldpost.php';
}
?>


<?php get_footer(); ?>