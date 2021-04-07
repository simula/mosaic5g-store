package it.polito.mec.video.raven.network_delay;

import com.google.gson.Gson;

import java.io.IOException;

import it.polito.mec.video.raven.RavenApplication;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;


public class SyncThread extends Thread {

        /*
        * reference https://en.wikipedia.org/wiki/Network_Time_Protocol
        * The time offset is computed as follows :
        * t0 - client time before request
        * t1 - server time upon receiving the request
        * t2 - server time when sending the response
        * t3 - client time when receiving the response
        *
        * time offset = ((t1-t0)+(t2-t3)) / 2
        * round trip delay = (t3-t0) - (t2-t1)
        * */

    private OkHttpClient client;
    public final MediaType JSON
            = MediaType.parse("application/json; charset=utf-8");

    private int SYNC_INTERVAL = 50000;
    private String mRemoteUrl = "http://" + "192.168.1.32:9090" + "/time";
    private final Object lock = new Object();

    private SyncMessage mSyncMessage = new SyncMessage();
    private long drift;
    private long roundtripdelay;

    private long[] delays_window = new long[8];
    private long[] offset_window = new long[8];
    private Gson mGson;

    public SyncThread(Gson gsonInstance) {
        super(SyncThread.class.getSimpleName());
        this.mGson = gsonInstance;
        client = new OkHttpClient();
        for (int i = 0; i < delays_window.length; i++) {
            delays_window[i] = Long.MIN_VALUE;
            offset_window[i] = Long.MIN_VALUE;
        }
    }

    public void setRemoteUrl(String ip, String port) {
        synchronized (lock) {
            mRemoteUrl = "http://" + ip + ":" + port + "/time";
            for (int i = 0; i < delays_window.length; i++) {
                delays_window[i] = Long.MIN_VALUE;
                offset_window[i] = Long.MIN_VALUE;
            }
        }
    }

    public long getDrift() {
        synchronized (lock) {
            return drift;
        }
    }

    @Override
    public void run() {
        while (!Thread.interrupted()) {
            try {
                synchronized (lock) {
                    mSyncMessage.timestamp_t0 = System.currentTimeMillis();
                    mSyncMessage = mGson.fromJson(post(mRemoteUrl, mGson.toJson(mSyncMessage)), SyncMessage.class);
                    mSyncMessage.timestamp_t3 = System.currentTimeMillis();

                    // Compute clock drift
                    drift = (mSyncMessage.timestamp_t1 - mSyncMessage.timestamp_t0 + mSyncMessage.timestamp_t2 - mSyncMessage.timestamp_t3) / 2;
                    roundtripdelay = mSyncMessage.timestamp_t3 - mSyncMessage.timestamp_t0 - mSyncMessage.timestamp_t2 + mSyncMessage.timestamp_t1;

                    System.arraycopy(offset_window, 0, offset_window, 1, offset_window.length - 1);
                    System.arraycopy(delays_window, 0, delays_window, 1, delays_window.length - 1);

                    offset_window[0] = drift;
                    delays_window[0] = roundtripdelay;

                    long accumulator = 0, count = 0;

                    for (int i = 0; i < offset_window.length; i++) {
                        if (offset_window[i] == Long.MIN_VALUE) {
                            break;
                        }
                        accumulator += offset_window[i] * (offset_window.length - i);
                        count += (offset_window.length - i);
                    }
                    drift = accumulator / count;

                    accumulator = 0;
                    count = 0;
                    for (int i = 0; i < delays_window.length; i++) {
                        if (delays_window[i] == Long.MIN_VALUE) {
                            break;
                        }
                        accumulator += delays_window[i] * (delays_window.length - i);
                        count += (offset_window.length - i);
                    }
                    roundtripdelay = accumulator / count;

                    mSyncMessage.timestamp_t1 = 0;
                    mSyncMessage.timestamp_t2 = 0;
                }
                sleep(SYNC_INTERVAL);
            } catch (InterruptedException exception) {
                //The thread has been interrupted, let's quit
                return;
            } catch (IOException exception) {
                //some IO problem, do not care
            }
        }
    }

    private String post(String url, String json) throws IOException {
        RequestBody body = RequestBody.create(JSON, json);
        Request request = new Request.Builder()
                .url(url)
                .post(body)
                .build();
        Response response = client.newCall(request).execute();
        return response.body().string();
    }
}
