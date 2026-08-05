<?php
/** Synthetic migration fixture for read-only evaluation. */
function fixture_migrate_orders(): void
{
    $offset = (int) get_option('fixture_migration_offset', 0);
    $orders = wc_get_orders(array(
        'limit'  => 100,
        'offset' => $offset,
        'return' => 'objects',
    ));

    update_option('fixture_migration_offset', $offset + count($orders));

    foreach ($orders as $order) {
        $order->update_meta_data('_fixture_migrated', 'yes');
        $order->save();
    }
}
