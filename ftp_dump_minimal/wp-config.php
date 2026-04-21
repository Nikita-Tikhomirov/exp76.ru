<?php
/**
 * The base configuration for WordPress
 *
 * The wp-config.php creation script uses this file during the
 * installation. You don't have to use the web site, you can
 * copy this file to "wp-config.php" and fill in the values.
 *
 * This file contains the following configurations:
 *
 * * MySQL settings
 * * Secret keys
 * * Database table prefix
 * * ABSPATH
 *
 * @link https://codex.wordpress.org/Editing_wp-config.php
 *
 * @package WordPress
 */

// ** MySQL settings - You can get this info from your web host ** //
/** The name of the database for WordPress */
define('WP_CACHE', true);
define( 'WPCACHEHOME', '/var/www/exp76248/data/www/exp76.ru/wp-content/plugins/wp-super-cache/' );
define('DB_NAME', 'exp76248_admin');

/** MySQL database username */
define('DB_USER', 'exp76248_admin');

/** MySQL database password */
define('DB_PASSWORD', 'X3a1V3f9');

/** MySQL hostname */
define('DB_HOST', 'localhost');

/** Database Charset to use in creating database tables. */
define('DB_CHARSET', 'utf8');

/** The Database Collate type. Don't change this if in doubt. */
define('DB_COLLATE', '');

/**#@+
 * Authentication Unique Keys and Salts.
 *
 * Change these to different unique phrases!
 * You can generate these using the {@link https://api.wordpress.org/secret-key/1.1/salt/ WordPress.org secret-key service}
 * You can change these at any point in time to invalidate all existing cookies. This will force all users to have to log in again.
 *
 * @since 2.6.0
 */
define('AUTH_KEY',         'N%dj!GEd*CaYd)^E3bbc6sP^zv)mO&l)z&ZVtLrgIxeT*t42QS)oc&(PpoewVKrp');
define('SECURE_AUTH_KEY',  'kdotGhnlu0PHG1V7@2%&jcpC&!D4Hzw6JWvFKMTS5tD2ya^)^dPIPpbBk9C40Kcj');
define('LOGGED_IN_KEY',    'yR(5K47It^7p0Hy!t^Fw#tOR@b%3*zOF9&Dl!2QHfHBZzGJ3VrFjxbldWJttLV1f');
define('NONCE_KEY',        'mfx5Io8Ncd61MP6!83wdd!*2!dpWN!rX#a4tyvWbJyxVU6l0b(^ky*54RGG%d(iq');
define('AUTH_SALT',        '*&57vJ2#XpNBGSthgz0(49hwFiCM%3C45N#Zle4u7L7IN(h%has%Pt8U4W604KdM');
define('SECURE_AUTH_SALT', 'yTOxL#ZtJpv5NpYUvG!NFkNRU9miRR2hiPWDQ@pkGwZ!2djwF*ZsRPNQwpS6d^fz');
define('LOGGED_IN_SALT',   'l@j66U0GUd1jUJ)E(m#fyP^J&VVVL7J9B&&XXK@HknZXz8*B2F)!ncCSBZ@Ez6MD');
define('NONCE_SALT',       'GsKkjAO6GRmtdFWkSlG0uQ2Qs&eiLvtdQr)Btm(t(fs7Wl0ReUHZevk8vC4Lyb9O');
define('WP_MEMORY_LIMIT', '256M');
/**#@-*/

/**
 * WordPress Database Table prefix.
 *
 * You can have multiple installations in one database if you give each
 * a unique prefix. Only numbers, letters, and underscores please!
 */
$table_prefix  = 'wp_';

/**
 * For developers: WordPress debugging mode.
 *
 * Change this to true to enable the display of notices during development.
 * It is strongly recommended that plugin and theme developers use WP_DEBUG
 * in their development environments.
 *
 * For information on other constants that can be used for debugging,
 * visit the Codex.
 *
 * @link https://codex.wordpress.org/Debugging_in_WordPress
 */
define('WP_DEBUG', false);
define( 'WP_DEBUG_LOG', false ); 

/* That's all, stop editing! Happy blogging. */

/** Absolute path to the WordPress directory. */
if ( !defined('ABSPATH') )
	define('ABSPATH', dirname(__FILE__) . '/');

/** Sets up WordPress vars and included files. */
require_once(ABSPATH . 'wp-settings.php');

define( 'WP_ALLOW_MULTISITE', true );

define ('FS_METHOD', 'direct');
