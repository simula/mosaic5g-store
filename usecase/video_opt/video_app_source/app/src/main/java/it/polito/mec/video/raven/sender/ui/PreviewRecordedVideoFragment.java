package it.polito.mec.video.raven.sender.ui;

import android.content.Context;
import android.os.Bundle;
import android.os.PowerManager;
import android.support.v4.app.Fragment;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.Surface;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.RelativeLayout;
import android.widget.TextView;
import android.widget.Toast;

import org.w3c.dom.Text;

import java.nio.channels.FileLock;
import java.text.BreakIterator;

import it.polito.mec.video.raven.R;
import it.polito.mec.video.raven.VideoChunks;
import it.polito.mec.video.raven.network_delay.Sync;
import it.polito.mec.video.raven.receiver.DecoderThread;
import it.polito.mec.video.raven.receiver.net.WSClientImpl;
import it.polito.mec.video.raven.receiver.ui.ReceiverMainActivity;

/**
 * Created by Jetmir on 16/01/2017.
 */
public class PreviewRecordedVideoFragment extends Fragment {

    private TextView mEncodingDetails, delayDetails;
    private Surface mSurface;
    private DecoderThread mDecoderTask;
    private PowerManager.WakeLock wakeLock;

    private SurfaceView outputView;
    private VideoListener mClient;
    private View qualityView;


    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
        RelativeLayout rootLayout = (RelativeLayout) inflater.inflate(R.layout.fragment_preview_video, container, false);
        outputView = (SurfaceView) rootLayout.findViewById(R.id.output_view);
        qualityView = rootLayout.findViewById(R.id.quality_indicator);
        qualityView.setVisibility(View.INVISIBLE);
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

        mEncodingDetails = (TextView) rootLayout.findViewById(R.id.encoding_details_tv);

        return rootLayout;
    }


    public VideoListener getVideoReceiverLocal() {
        mClient = new VideoListener() {

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

            @Override
            public void onStreamChunkReceived(byte[] chunk, int flags, long timestamp, long latency) {

                VideoChunks.Chunk c = new VideoChunks.Chunk(chunk, flags, timestamp);
                mDecoderTask.submitEncodedData(c);

            }

            @Override
            public void setQuality(String quality) {
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
        };
        return mClient;
    }

    @Override
    public void onPause() {
        stopDecoder();
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
    public void onResume() {
        super.onResume();
        PowerManager pm = (PowerManager) getActivity().getSystemService(Context.POWER_SERVICE);
        wakeLock = pm.newWakeLock(
                PowerManager.SCREEN_DIM_WAKE_LOCK | PowerManager.ON_AFTER_RELEASE,
                "My wakelook");
        wakeLock.acquire();
    }

    public Fragment setVideoSource(PreviewFragment previewFragment) {
        return this;
    }
}
