package it.polito.mec.video.raven.sender.ui;

/**
 * Created by Jetmir on 16/01/2017.
 */
public interface VideoListener {
    void onConfigParamsReceived(byte[] configParams, final int width, final int height, final int bitrate);
    void onStreamChunkReceived(byte[] chunk, int flags, long timestamp, long latency);

    void setQuality(String quality);
}
