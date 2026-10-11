# UGOT Python SDK quick reference

Condensed from the official UGOT product manual (SDK v0.2.12, system v1.7.0.3 or above). Install with `pip install ugot`. Direction codes below are the ones the SDK uses everywhere.

## Setup

```python
from ugot import ugot
got = ugot.UGOT()
got.scan_device()              # dict {"name": "ip"} of UGOT devices on the LAN
got.initialize("192.168.x.x")  # IP is under Settings > About on the robot
```

The computer and the robot must be on the same network.

## Conventions

```
direction (move)  0 = forward, 1 = backward   (spider/dog translate: 2 = left, 3 = right)
turn              2 = LEFT turn, 3 = RIGHT turn
unit (move)       0 = seconds, 1 = centimetres
unit (turn)       0 = seconds, 2 = degrees
lock (stop)       False = unlock after stop (default), True = hold position
```

Speed limits: move 0-80 cm/s (mecanum, transform, balance), 5-60 wheelleg, 0-25 spider and dog. Turn 5-280 deg/s mecanum and transform, 5-360 balance, 5-180 wheelleg, 0-60 spider, 0-20 dog.

## Mecanum vehicle (used in Level 5 notebooks)

```
mecanum_move_speed(direction, speed)               continuous forward/backward
mecanum_turn_speed(turn, speed)                    continuous spin; 2 = left, 3 = right
mecanum_translate_speed(angle, speed)              slide; angle -180..180, 0 = forward, left negative, right positive
mecanum_move_xyz(x_speed, y_speed, z_speed)        x,y -80..80, z -280..280
mecanum_move_turn(angle, speed, turn, turn_speed)  slide while rotating
mecanum_move_speed_times(direction, speed, times, unit)
mecanum_turn_speed_times(turn, speed, times, unit)
mecanum_translate_speed_times(angle, speed, times, unit)
mecanum_motor_control(lf, rf, lb, rb)              per-wheel RPM, -360..360
mecanum_stop()
```

Generic chassis: `stop_chassis()`, `model_common_move(speed, turn_speed)` (positive turn_speed = left), `perform_action(name)`.

Other chassis follow the same pattern with a prefix: `transform_`, `balance_` (plus `balance_start_balancing`, `balance_stop_balancing`, `balance_set_acceleration`), `wheelleg_` (start/stop balancing, `set_chassis_height` 1-3, `set_decline_angle`), `spider_`, `dog_` (`dog_perform_action`), each with `restory()` to reset. `transform_set_chassis_height` takes 2-7 cm.

## Camera

```
got.open_camera()
raw = got.read_camera_data()   # bytes (JPEG), or None when no frame
frame = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)   # BGR, 640 wide
```

## Built-in AI vision

```
got.load_models([...])    names: human_pose, word_recognition, color_recognition,
                          apriltag_qrcode, face_attribute, lpd_recognition, gesture,
                          traffic_sign, face_recognition, line_recognition
                          returns True/False
got.release_models(models=None)    None = unload all

get_qrcode_total_info()        -> [[text, cx, cy, h, w, area], ...]
get_apriltag_total_info()      -> [[id, cx, cy, h, w, area, dist5, dist7, dist10, x, y, z, bearing_h, bearing_v], ...]
get_license_plate_total_info() -> [[number, type, cx, cy, h, w, area], ...]
get_pose_total_info()          -> [[17 keypoints as x,y pairs], ...]
get_traffic_total_info()       -> [[sign, cx, cy, h, w, area], ...]
get_face_recognition_total_info() -> [[name, cx, cy, h, w, area], ...]   "Unknown" if not registered
face_recognition_add_name(name) / _delete_name(name) / _get_all_names()
get_face_characteristic_total_info() -> [[gender, mask, emotion, cx, cy, h, w, area], ...]
get_color_total_info()         -> [color, shape, cx, cy, h, w, area]   one object only
get_words_result()             -> str
get_gesture_result()           -> "Stone" | "Scissor" | "Cloth" | "OK" | "Likes"
set_track_recognition_line(0 single | 1 double)
get_single_track_total_info()  -> [offset, type, x, y]    type 0 none, 1 straight, 2 Y, 3 crossroad
get_double_track_total_info()  -> [offset, type, x, y]    type 0 none, 1 straight, 2 intersection
```

KNN (on-robot training): `knn_train(model, labels)`, `get_knn_result(model)` (dict label -> confidence), `knn_rename`, `knn_delete`, `knn_query`.

## Sensors and device

```
read_distance_data(id)   cm, -1 if no data
read_gyro_data()         [pitch, roll, yaw, gyro_xyz, accel_xyz]
get_attitude()           [lean_fwd, lean_back, lean_left, lean_right, screen_up, screen_down, shake]
get_power_status()       [percent, plugged, status 0 normal/1 low/2 charging/3 full/4 abnormal]
get_wifi_status(), get_mac_address(), get_device_name(), get_peripheral_devices_list()
get_joypad_pressing_buttons(), get_joypad_coordinate()   [LX, LY, RX, RY] each -255..255
```

## Servo, motor, arm

```
turn_servo_angle(id, angle, duration_ms, wait=False)   angle -180..180, duration 20..5000
turn_servo_speed(id, speed)  -100..100        turn_servo_speed_times(id, speed, secs)
read_servo_angle(id) -> dict                  stop_servo(id, lock=False)
turn_motor_speed(id, speed)  -140..140        turn_motor_speed_times(id, speed, secs)
turn_motor_angle(id, angle, duration_ms, wait=False)   read_motor_speed / read_motor_angle -> dict
stop_motor(id, lock=False)                    stop_all_servos()
```

`id` may be an int or a list of ints.

Mechanical arm: `mechanical_clamp_release()`, `mechanical_clamp_close()`, `mechanical_get_clamp_status()` (0 open, 1 closed), `mechanical_arms_restory()`, `mechanical_joint_control(a1, a2, a3, ms)` (ranges -90..90, -80..110, -90..90), `mechanical_single_joint_control(joint, angle, ms)`, `mechanical_move_axis(r, h, theta, ms)` (r -5.5..24.9 cm, h -18..18.2 cm, theta -1.57..1.57 rad).

## Sound, speech, screen, lights

```
play_sound(name, wait=False)      built-in effects (animals, emotions, machines, commands)
play_tone(tone, beat, wait=False) tone C5..C6, beat 0=1/8 1=1/4 2=1/2 3=1 4=2
play_audio_tts(text, voice_type=0, wait=False)   0 female, 1 male
start_audio_asr() -> str          start_audio_nlp(question, wait=False)
start_audio_asr_doa(duration=60) -> [direction, text]
enable_audio_direction(), get_audio_direction(), disable_audio_direction()
set_volume(0-100), get_volume() -> [volume, isMute], stop_audio()
screen_display_background(c), screen_print_text(t, c), screen_print_text_newline(t, c),
screen_clear(), screen_display_emotion(name, loop=False)
   colours: 0 black 1 white 2 purple 3 red 4 orange 5 yellow 6 green 7 cyan 8 blue
show_light_rgb(lights, r, g, b)   lights = list of 0 top, 1 left, 2 right, 3 bottom
show_light_hsv(lights, h, s, v)   each 0-100
show_light_rgb_effect(r, g, b, effect)   effect 0 steady, 1 off, 2 breathing, 3 blinking
show_light_hsv_effect(h, s, v, effect), turn_off_lights()
```

## PID, pins, broadcast

```
pid = got.create_pid_controller()      # the manual's older sample uses ugot.PID(); both appear
pid.set_pid(kp, ki, kd)
output = pid.update(error)
```

```
set_pin_level(pin, bool), read_pin_level(pin)       pins 4, 5, 6
set_pin_pwm(pin, 0-255)                             pins 1, 2
set_pin_pwm_duty_cycle(pin, frequency 10..980, duty 0.0..100.0)
serial: set_serial_serbaud, write_serial_string(newline, text), write_serial_number,
        read_serial_byte, read_serial_string, read_serial_string_until(char), clear_gpio_serial
enable_broadcast(), disable_broadcast(), set_broadcast_channel(0-99),
send_broadcast_message(str), get_broadcast_message()
```

## Known manual inconsistencies

The manual's QR/AprilTag sample calls `get_qrcode_apriltag_total_info()`, but the documented functions are `get_qrcode_total_info()` and `get_apriltag_total_info()`. The `stop_servo` and `stop_motor` headings omit the `lock` parameter that their descriptions list. Several samples in the manual were mangled by conversion (statements merged onto one line); trust the interface lists above, not the sample layout.

## Teaching patterns from the manual

Line following: read `offset` from the single-track info, feed it to a PID (the manual uses kp about 0.23, ki and kd 0), then turn by the output. Ball grabbing: use the pixel gap between the target's `center_x` and 320 as the PID error to turn, and the distance sensor to approach. Both are closed-loop versions of the bear-centring loop in L5204T1.
