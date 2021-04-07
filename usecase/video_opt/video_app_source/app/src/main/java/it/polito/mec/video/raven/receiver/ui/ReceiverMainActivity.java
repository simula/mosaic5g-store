package it.polito.mec.video.raven.receiver.ui;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.PowerManager;
import android.preference.PreferenceManager;
import android.support.v7.app.AppCompatActivity;
import android.util.Log;
import android.view.Surface;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import it.polito.mec.video.raven.R;
import it.polito.mec.video.raven.VideoChunks;
import it.polito.mec.video.raven.network_delay.Sync;
import it.polito.mec.video.raven.receiver.DecoderThread;
import it.polito.mec.video.raven.receiver.net.WSClientImpl;


public class ReceiverMainActivity extends AppCompatActivity {

    private Button mConnectionButton;
    private TextView mEncodingDetails, delayDetails;
    private Surface mSurface;
    private DecoderThread mDecoderTask;

    private PowerManager.WakeLock wakeLock;
    private SharedPreferences mPreferences;

    private WSClientImpl mClient;
    private String serverIp;
    private String serverPort_s;
    private View qualityView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_receiver);

        qualityView = findViewById(R.id.quality_indicator);
        qualityView.setVisibility(View.INVISIBLE);

        mClient = new WSClientImpl(new WSClientImpl.Listener() {
            @Override
            public void onConnectionLost(boolean closedByServer) {
                Toast.makeText(ReceiverMainActivity.this, "Connection lost : closed by server " + closedByServer, Toast.LENGTH_LONG).show();
                ((Sync) getApplication()).stopSyncing();
                setupConnectionButton(true);
            }

            @Override
            public void onConnectionEstablished() {
                Toast.makeText(ReceiverMainActivity.this, "Connected", Toast.LENGTH_LONG).show();
                ((Sync) getApplication()).setRemoteSyncUrl(serverIp, serverPort_s);
                setupConnectionButton(false);
            }

            @Override
            public void onConnectionFailed(Exception e) {
                Toast.makeText(ReceiverMainActivity.this, "Can't connect to server: "
                        + e.getClass().getSimpleName() + ": " + e.getMessage(), Toast.LENGTH_LONG).show();

            }

            @Override
            public void onConfigParamsReceived(byte[] configParams, final int width, final int height, final int bitrate) {
                Log.d("ACT", "config bytes[" + configParams.length + "] ; " +
                        "resolution: " + width + "x" + height + " " + bitrate + " Kbps");
                stopDecoder();
                startDecoder(width, height, configParams);
                mEncodingDetails.post(new Runnable() {
                    @Override
                    public void run() {
                        mEncodingDetails.setText(String.format("(%dx%d) %d Kbps", width, height, bitrate));
                    }
                });
            }

            int counter = 0;
            private long mLatency = 0;

            @Override
            public void onStreamChunkReceived(byte[] chunk, int flags, long timestamp, long latency) {
                mLatency = (mLatency * 10 + latency) / 11;

                VideoChunks.Chunk c = new VideoChunks.Chunk(chunk, flags, timestamp);
                mDecoderTask.submitEncodedData(c);

                if (counter++ % 10 == 0) {

                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            delayDetails.setText("D : " + mLatency);
                        }
                    });
                }
            }

            @Override
            public void onQualitychanged(String quality) {
                if (quality != null) {
                    switch (quality.toLowerCase()) {
                        case "medium":
                            qualityView.setBackgroundResource(R.drawable.round_yellow);
                            break;
                        case "low":
                            qualityView.setBackgroundResource(R.drawable.round_red);
                            break;
                        case "high":
                            qualityView.setBackgroundResource(R.drawable.round_green);
                            break;
                    }
                    qualityView.setVisibility(View.VISIBLE);
                } else {
                    qualityView.setVisibility(View.INVISIBLE);
                }
            }
        }, (Sync) getApplication());

        mConnectionButton = (Button) findViewById(R.id.connect_button);
        mEncodingDetails = (TextView) findViewById(R.id.encoding_details_tv);
        delayDetails = (TextView) findViewById(R.id.delay_details);
        //Toolbar toolbar = (Toolbar) findViewById(R.id.toolbar);
        //setSupportActionBar(toolbar);

        final SurfaceView outputView = (SurfaceView) findViewById(R.id.output_view);
        outputView.getHolder().addCallback(new SurfaceHolder.Callback() {
            @Override
            public void surfaceCreated(SurfaceHolder holder) {

            }

            @Override
            public void surfaceChanged(SurfaceHolder holder, int format, int width, int height) {
                mSurface = holder.getSurface();
            }

            @Override
            public void surfaceDestroyed(SurfaceHolder holder) {

            }
        });

        setupConnectionButton(true);



        mPreferences = PreferenceManager.getDefaultSharedPreferences(this);
    }

    private void setupConnectionButton(boolean connect) {
        String text = connect ? "Connect" : "Disconnect";
        View.OnClickListener listener;
        if (connect) {
            listener = new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    serverIp = mPreferences.getString(getString(R.string.pref_key_server_ip),
                            getString(R.string.pref_server_ip_default_value));
                    serverPort_s = mPreferences.getString(getString(R.string.pref_key_server_port),
                            getString(R.string.pref_server_port_default_value));
                    int port = Integer.parseInt(serverPort_s);
                    mClient.connect(serverIp, port, 2000);
                }
            };
        } else {
            listener = new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    mClient.closeConnection();
                }
            };
        }
        mConnectionButton.setText(text);
        mConnectionButton.setOnClickListener(listener);
    }

    @Override
    protected void onPause() {
        stopDecoder();
        if (mClient.getSocket() != null) {
            mClient.closeConnection();
        }
        wakeLock.release();
        super.onPause();
    }

    private void startDecoder(int width, int height, byte[] configParams) {
        if (mDecoderTask == null) {
            mDecoderTask = new DecoderThread(width, height);
            mDecoderTask.setSurface(mSurface);
            mDecoderTask.setConfigurationBuffer(configParams);
            mDecoderTask.start();
        }
    }

    private void stopDecoder() {
        if (mDecoderTask != null) {
            mDecoderTask.interrupt();
            try {
                mDecoderTask.join();
            } catch (InterruptedException e) {
            }
            mDecoderTask = null;
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        PowerManager pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
        wakeLock = pm.newWakeLock(
                PowerManager.SCREEN_DIM_WAKE_LOCK | PowerManager.ON_AFTER_RELEASE,
                "My wakelook");
        wakeLock.acquire();
    }

}
