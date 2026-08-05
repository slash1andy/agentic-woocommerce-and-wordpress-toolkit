<?php
/**
 * Plugin Name: Fixture Commerce Extension
 * Requires PHP: 7.4
 * WC requires at least: 8.0
 */

declare(strict_types=1);

namespace FixtureCommerce;

defined('ABSPATH') || exit;

add_action('plugins_loaded', static function (): void {
    if (! class_exists('WooCommerce')) {
        return;
    }

    Plugin::init();
});

final class Plugin
{
    public static function init(): void
    {
        do_action('fixture_commerce_loaded');
    }
}
