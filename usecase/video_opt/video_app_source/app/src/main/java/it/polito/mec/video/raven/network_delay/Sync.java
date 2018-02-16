package it.polito.mec.video.raven.network_delay;

/**
 * Created by Jetmir on 12/01/2017.
 */

public interface Sync {
    void setRemoteSyncUrl(String ip, String port);

    void logFrameDelay(int dealyMillis);

    void startSyncing();

    void stopSyncing();

    long getDrift();
}
