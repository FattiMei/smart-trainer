#include <stdio.h>

int main() {
    int ev[20] = {100, 120, 160, 340, 500, 660, 680, 750, 920, 1000,
                    1550, 2000, 2010, 2060, 3000, 3040, 3090, 3200, 3460, 3500}; // event[event_number] = {event times} HARDCODATA
    int valid_ev[20][2];  // valid_event[max_event_number][start_time, end_time]
    int count_valid_ev = 0;
    float uwb[4000][1];  // uwb[times][value]
    int overlap_threshold = 5; // 50ms
    int uwb_window_size = 30; // 300ms
    int uwb_windows[150][3]; // uwb_windows[max_windows][start_time, end_time, boolean_event_exist]
    int num_windows = 0;

    for (int i = 1; i < 20; i++) {
        if(ev[i] - ev[i-1] > 29 && ev[i] - ev[i-1] < 151) {  // 200bpm/60sec = 0.3s, 40bpm/60sec = 1.5s
            valid_ev[count_valid_ev][0] = ev[i-1];
            valid_ev[count_valid_ev][1] = ev[i];

            count_valid_ev++;
        }
    }

    printf("coppie di battiti consecutivi validi:\n");

    for (int i = 0; i < count_valid_ev; i++) {
        printf("(%d, %d)\n", valid_ev[i][0], valid_ev[i][1]);
    }

    for(int i = 0; i < count_valid_ev; i++) {
        for(int t = valid_ev[i][0]; t <= valid_ev[i][1]; t += overlap_threshold) {
            uwb_windows[num_windows][0] = t - uwb_window_size/2;
            uwb_windows[num_windows][1] = t + uwb_window_size/2;;
            
            // se l'evento cade sul bordo della finestra come lo considero? ORA NON LO CONSIDERO
            // se due coppie di eventi sono adiacenti allora l'ultima finestra e la prima della successiva sono uguali
            // come le gestisco? ORA LE CONSIDERO DIVERSE
            if((valid_ev[i][0] > uwb_windows[num_windows][0] && valid_ev[i][0] < uwb_windows[num_windows][1]) || 
               (valid_ev[i][1] > uwb_windows[num_windows][0] && valid_ev[i][1] < uwb_windows[num_windows][1])){
                uwb_windows[num_windows][2] = 1; // set boolean_event_exist to true
            }else{
                uwb_windows[num_windows][2] = 0; // set boolean_event_exist to false
            }

            num_windows++;
        }
    }

    printf("finestre UWB tra eventi:\n");

    for (int i = 0; i < num_windows; i++) {
        printf("(%d, %d, %d)\n", uwb_windows[i][0], uwb_windows[i][1], uwb_windows[i][2]);
    }

};