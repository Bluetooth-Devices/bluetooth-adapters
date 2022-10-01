# Changelog

<!--next-version-placeholder-->

## v0.5.3 (2022-10-01)
### Fix
* Compat with upcoming bleak ([#20](https://github.com/Bluetooth-Devices/bluetooth-adapters/issues/20)) ([`61fcdbf`](https://github.com/Bluetooth-Devices/bluetooth-adapters/commit/61fcdbfd6865df17dda8369bf7b26ae51ed49d20))

## v0.5.2 (2022-09-26)
### Fix
* Handle ConnectionRefusedError ([#19](https://github.com/Bluetooth-Devices/bluetooth-adapters/issues/19)) ([`7e85613`](https://github.com/Bluetooth-Devices/bluetooth-adapters/commit/7e85613cb2f972773748b4cde4ba826f75d807d2))

## v0.5.1 (2022-09-17)
### Fix
* Restoring manufacturer_data ([#18](https://github.com/Bluetooth-Devices/bluetooth-adapters/issues/18)) ([`264d63a`](https://github.com/Bluetooth-Devices/bluetooth-adapters/commit/264d63a93af8aae9cfb4c4f75e2f1632366edb20))

## v0.5.0 (2022-09-17)
### Feature
* Add support for restoring bluetooth history from the bus ([#17](https://github.com/Bluetooth-Devices/bluetooth-adapters/issues/17)) ([`3aaf104`](https://github.com/Bluetooth-Devices/bluetooth-adapters/commit/3aaf104fe5798285f995e840310ea06f3d6a9a4d))

## v0.4.1 (2022-09-10)
### Fix
* Bump dbus-fast ([#16](https://github.com/Bluetooth-Devices/bluetooth-adapters/issues/16)) ([`6e665ae`](https://github.com/Bluetooth-Devices/bluetooth-adapters/commit/6e665ae38834e42d849ac33db228a9aa6578ddeb))

## v0.4.0 (2022-09-09)
### Feature
* Switch from dbus-next to dbus-fast ([#15](https://github.com/Bluetooth-Devices/bluetooth-adapters/issues/15)) ([`90d9ca5`](https://github.com/Bluetooth-Devices/bluetooth-adapters/commit/90d9ca50ac687ecef129c0a080242ce8daa0edda))

## v0.3.6 (2022-09-09)
### Fix
* Handle Dbus closing the connection on us ([#14](https://github.com/Bluetooth-Devices/bluetooth-adapters/issues/14)) ([`847698f`](https://github.com/Bluetooth-Devices/bluetooth-adapters/commit/847698f14001b41790412e8cec38369ccb117402))

## v0.3.5 (2022-09-08)
### Fix
* Downgrade more loggers to debug in case they do not have bluez installed and do not want bluetooth ([#13](https://github.com/Bluetooth-Devices/bluetooth-adapters/issues/13)) ([`cae2700`](https://github.com/Bluetooth-Devices/bluetooth-adapters/commit/cae2700f26b06f461647875f48e0f8a1baae298c))

## v0.3.4 (2022-09-02)
### Fix
* Downgrade more loggers ([#12](https://github.com/Bluetooth-Devices/bluetooth-adapters/issues/12)) ([`3deb74f`](https://github.com/Bluetooth-Devices/bluetooth-adapters/commit/3deb74f2ddd10738029b64d9865a6cbeada83b7b))

## v0.3.3 (2022-09-01)
### Fix
* Downgrade dbus timeouts to debug logging as it likely means they have no bluez ([#11](https://github.com/Bluetooth-Devices/bluetooth-adapters/issues/11)) ([`4f6ae64`](https://github.com/Bluetooth-Devices/bluetooth-adapters/commit/4f6ae64c22711022be449c19adc9bd97b2769846))

## v0.3.2 (2022-08-27)
### Fix
* Seperate FileNotFoundError and BrokenPipeError errors ([#10](https://github.com/Bluetooth-Devices/bluetooth-adapters/issues/10)) ([`f0b3d81`](https://github.com/Bluetooth-Devices/bluetooth-adapters/commit/f0b3d81d65586e536b78055426bd7118d1803587))

## v0.3.1 (2022-08-27)
### Fix
* Manage BrokenPipeError thrown by MessageBus.connect() ([#9](https://github.com/Bluetooth-Devices/bluetooth-adapters/issues/9)) ([`5d0fbaa`](https://github.com/Bluetooth-Devices/bluetooth-adapters/commit/5d0fbaa1533924c2e256a1a682c6ea7982cf8ed7))

## v0.3.0 (2022-08-27)
### Feature
* Add get_dbus_managed_objects ([#8](https://github.com/Bluetooth-Devices/bluetooth-adapters/issues/8)) ([`ce613ea`](https://github.com/Bluetooth-Devices/bluetooth-adapters/commit/ce613ea7fcdda5fdacfc8848ed2a1ef290e64b92))

## v0.2.0 (2022-08-18)
### Feature
* Add get_bluetooth_adapter_details ([#7](https://github.com/Bluetooth-Devices/bluetooth-adapters/issues/7)) ([`619f1ac`](https://github.com/Bluetooth-Devices/bluetooth-adapters/commit/619f1acc9efd953ff57c9f126f64c21579b65e7e))

## v0.1.3 (2022-08-01)
### Fix
* Add a timeout in case dbus fails to respond ([#6](https://github.com/Bluetooth-Devices/bluetooth-adapters/issues/6)) ([`eff1022`](https://github.com/Bluetooth-Devices/bluetooth-adapters/commit/eff10222a6f1e0be4a599e6e47f20bace4ffd711))

## v0.1.2 (2022-07-24)
### Fix
* Adapters now returns a list instead of a set since order matters ([#5](https://github.com/Bluetooth-Devices/bluetooth-adapters/issues/5)) ([`b4f153b`](https://github.com/Bluetooth-Devices/bluetooth-adapters/commit/b4f153bf4198ad34e9e12113272c798fd6bddad6))

## v0.1.1 (2022-07-22)
### Fix
* Disconnect is not a coro ([#4](https://github.com/Bluetooth-Devices/bluetooth-adapters/issues/4)) ([`05022b2`](https://github.com/Bluetooth-Devices/bluetooth-adapters/commit/05022b20cc55bff8fe927dadd746d7879085f702))

## v0.1.0 (2022-07-22)
### Feature
* Bump to resync verison ([#3](https://github.com/Bluetooth-Devices/bluetooth-adapters/issues/3)) ([`d0ec824`](https://github.com/Bluetooth-Devices/bluetooth-adapters/commit/d0ec82419d96052c8315a0518622b794bbb502d2))
