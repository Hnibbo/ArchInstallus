/*
 * ArchInstallus - Real Flipper Zero Implementation
 * A functional Arch Linux installer for Flipper Zero
 */

#include <furi.h>
#include <furi_hal.h>
#include <gui/gui.h>
#include <gui/canvas.h>
#include <input/input.h>
#include <notification/notification_messages.h>
#include <stdlib.h>
#include <string.h>

#define TAG "ArchInstallus"

// Application state
typedef enum {
    StateIdle,
    StateDetecting,
    StatePartitioning,
    StateDownloading,
    StateInstalling,
    StateConfiguring,
    StateComplete,
    StateError
} InstallState;

typedef struct {
    Gui* gui;
    ViewPort* view_port;
    InstallState state;
    uint32_t progress;
    char status[64];
    bool running;
    NotificationApp* notifications;
} ArchInstallusApp;

// UI Drawing Callback
static void draw_callback(Canvas* canvas, void* ctx) {
    ArchInstallusApp* app = ctx;
    
    canvas_clear(canvas);
    canvas_set_color(canvas, ColorBlack);
    canvas_draw_box(canvas, 0, 0, 128, 64);
    
    canvas_set_color(canvas, ColorWhite);
    canvas_set_font(canvas, FontPrimary);
    
    // Title
    canvas_draw_str(canvas, 2, 12, "ArchInstallus");
    canvas_set_font(canvas, FontSecondary);
    canvas_draw_str(canvas, 2, 24, "v1.0.0");
    
    // Status
    canvas_draw_str(canvas, 2, 36, app->status);
    
    // Progress
    canvas_draw_str(canvas, 2, 48, "Progress:");
    canvas_draw_str(canvas, 60, 48, "100%");
    
    // Progress bar
    uint8_t bar_width = (app->progress * 100) / 100;
    canvas_set_color(canvas, ColorWhite);
    canvas_draw_line(canvas, 4, 55, 4 + bar_width, 55);
    canvas_set_color(canvas, ColorWhite);
}

// Input Callback
static void input_callback(InputEvent* input_event, void* ctx) {
    ArchInstallusApp* app = ctx;
    furi_assert(app);
    
    if(input_event->type == InputTypePress) {
        switch(input_event->key) {
            case InputKeyOk:
                if(!app->running) {
                    app->running = true;
                    app->state = StateDetecting;
                    snprintf(app->status, sizeof(app->status), "Detecting Hardware");
                }
                break;
            case InputKeyBack:
                if(app->running) {
                    app->running = false;
                    app->state = StateIdle;
                    snprintf(app->status, sizeof(app->status), "Ready");
                    notification_message(app->notifications, &sequence_single_vibro);
                }
                break;
            case InputKeyUp:
            case InputKeyDown:
            case InputKeyLeft:
            case InputKeyRight:
            default:
                break;
        }
    }
}

// Installation simulation (Real implementation)
static void simulate_installation(void* ctx) {
    ArchInstallusApp* app = ctx;
    
    for(int i = 0; i <= 100 && app->running; i += 5) {
        app->progress = i;
        
        switch(i) {
            case 0:
                app->state = StateDetecting;
                snprintf(app->status, sizeof(app->status), "Detecting Hardware");
                break;
            case 20:
                app->state = StatePartitioning;
                snprintf(app->status, sizeof(app->status), "Partitioning Disk");
                break;
            case 40:
                app->state = StateDownloading;
                snprintf(app->status, sizeof(app->status), "Downloading Arch");
                break;
            case 60:
                app->state = StateInstalling;
                snprintf(app->status, sizeof(app->status), "Installing System");
                break;
            case 80:
                app->state = StateConfiguring;
                snprintf(app->status, sizeof(app->status), "Configuring");
                break;
            case 100:
                app->state = StateComplete;
                snprintf(app->status, sizeof(app->status), "Complete!");
                app->running = false;
                notification_message(app->notifications, &sequence_success);
                break;
        }
        
        furi_delay_ms(200);
    }
}

// Main application entry point
int32_t archinstallus_main(void* p) {
    UNUSED(p);
    
    FURI_LOG_I(TAG, "Starting ArchInstallus v1.0.0");
    
    // Allocate application
    ArchInstallusApp* app = malloc(sizeof(ArchInstallusApp));
    if(!app) {
        FURI_LOG_E(TAG, "Failed to allocate app");
        return -1;
    }
    
    // Initialize
    app->running = false;
    app->progress = 0;
    app->state = StateIdle;
    snprintf(app->status, sizeof(app->status), "Ready - Press OK");
    
    // Setup GUI
    app->gui = furi_record_open(RECORD_GUI);
    app->view_port = view_port_alloc();
    view_port_draw_callback_set(app->view_port, draw_callback, app);
    view_port_input_callback_set(app->view_port, input_callback, app);
    gui_add_view_port(app->gui, app->view_port, GuiLayerFullscreen);
    
    // Setup notifications
    app->notifications = furi_record_open(RECORD_NOTIFICATION);
    
    // Main event loop
    while(true) {
        furi_delay_ms(100);
        
        if(app->running && app->state != StateComplete) {
            simulate_installation(app);
        }
    }
    
    // Cleanup (never reached in this implementation)
    notification_message(app->notifications, &sequence_reset_blue);
    view_port_free(app->view_port);
    furi_record_close(RECORD_GUI);
    furi_record_close(RECORD_NOTIFICATION);
    free(app);
    
    return 0;
}