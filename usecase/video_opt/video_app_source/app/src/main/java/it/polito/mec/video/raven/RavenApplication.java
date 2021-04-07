package it.polito.mec.video.raven;

import android.app.Application;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import it.polito.mec.video.raven.network_delay.Sync;
import it.polito.mec.video.raven.network_delay.SyncThread;

/**
 * Created by Jetmir on 11/01/2017.
 */

public class RavenApplication extends Application implements Sync {

    private SyncThread mSyncThread;
    private Gson mGson;

    @Override
    public void onCreate() {
        GsonBuilder builder = new GsonBuilder();
        mGson = builder.create();
    }

    public void setRemoteSyncUrl(String ip, String port) {
        if (mSyncThread != null) {
            mSyncThread.interrupt();
            mSyncThread = null;
        }
        mSyncThread = new SyncThread(mGson);
        mSyncThread.setRemoteUrl(ip, port);
        mSyncThread.start();
    }

    @Override
    public void logFrameDelay(int dealyMillis) {

    }

    public void startSyncing() {
        mSyncThread.start();
    }

    public void stopSyncing() {
        mSyncThread.interrupt();
        try {
            mSyncThread.join();
        } catch (InterruptedException ex) {

        }
    }

    public long getDrift() {
        return mSyncThread.getDrift();
    }

}
