package com.bakkle.bakkle.AddItem.MaterialCamera.internal;

import android.app.Activity;
import android.app.Fragment;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.media.MediaRecorder;
import android.os.Bundle;
import android.os.Handler;
import android.support.annotation.NonNull;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageButton;
import android.widget.TextView;

import com.afollestad.materialdialogs.DialogAction;
import com.afollestad.materialdialogs.MaterialDialog;
import com.bakkle.bakkle.AddItem.MaterialCamera.MaterialCamera;
import com.bakkle.bakkle.AddItem.MaterialCamera.util.CameraUtil;
import com.bakkle.bakkle.AddItem.MaterialCamera.util.Degrees;
import com.bakkle.bakkle.R;

import java.io.File;

import static android.app.Activity.RESULT_CANCELED;
import static com.bakkle.bakkle.AddItem.MaterialCamera.internal.BaseCaptureActivity.CAMERA_POSITION_BACK;

/**
 * @author Aidan Follestad (afollestad)
 */
abstract class BaseCameraFragment extends Fragment
        implements CameraUriInterface, View.OnClickListener
{

    protected ImageButton mButtonVideo;
    protected ImageButton mButtonPicture;
    protected ImageButton mButtonFacing;
    protected TextView    mRecordDuration;

    protected static final float PREFERRED_ASPECT_RATIO = 4f / 3f;
    protected static final int   PREFERRED_PIXEL_HEIGHT = 480;

    private   boolean              mIsRecording;
    protected String               mOutputUri;
    protected BaseCaptureInterface mInterface;
    protected Handler              mPositionHandler;
    protected MediaRecorder        mMediaRecorder;

    protected static void LOG(Object context, String message)
    {
        Log.d(context instanceof Class<?> ? ((Class<?>) context).getSimpleName() : context.getClass()
                .getSimpleName(), message);
    }

    private final Runnable mPositionUpdater = new Runnable()
    {
        @Override
        public void run()
        {
            if (mInterface == null || mRecordDuration == null) {
                return;
            }
            final long mRecordStart = mInterface.getRecordingStart();
            final long mRecordEnd = mInterface.getRecordingEnd();
            if (mRecordStart == -1 && mRecordEnd == -1) {
                return;
            }
            final long now = System.currentTimeMillis();
            if (mRecordEnd != -1) {
                if (now >= mRecordEnd) {
                    stopRecordingVideo(true);
                } else {
                    final long diff = mRecordEnd - now;
                    mRecordDuration.setText(
                            String.format("-%s", CameraUtil.getDurationString(diff)));
                }
            } else {
                mRecordDuration.setText(CameraUtil.getDurationString(now - mRecordStart));
            }
            if (mPositionHandler != null) {
                mPositionHandler.postDelayed(this, 1000);
            }
        }
    };

    @Override
    public final View onCreateView(LayoutInflater inflater, ViewGroup container,
                                   Bundle savedInstanceState)
    {
        return inflater.inflate(R.layout.mcam_fragment_videocapture, container, false);
    }

    @Override
    public void onViewCreated(View view, Bundle savedInstanceState)
    {
        super.onViewCreated(view, savedInstanceState);

        mButtonVideo = (ImageButton) view.findViewById(R.id.video);
        mButtonPicture = (ImageButton) view.findViewById(R.id.picture);
        mButtonFacing = (ImageButton) view.findViewById(R.id.facing);
        mRecordDuration = (TextView) view.findViewById(R.id.recordDuration);
        mButtonFacing.setImageResource(
                mInterface.getCurrentCameraPosition() == CAMERA_POSITION_BACK ? R.drawable.mcam_camera_front : R.drawable.mcam_camera_rear);
        if (mMediaRecorder != null && mIsRecording) {
            mButtonVideo.setImageResource(R.drawable.mcam_action_stop);
        } else {
            mButtonVideo.setImageResource(R.drawable.ic_videocam);
            mInterface.setDidRecord(false);
        }

        mButtonVideo.setOnClickListener(this);
        mButtonPicture.setOnClickListener(this);
        mButtonFacing.setOnClickListener(this);

        final int primaryColor = getArguments().getInt(
                com.bakkle.bakkle.AddItem.MaterialCamera.internal.CameraIntentKey.PRIMARY_COLOR);
        view.findViewById(R.id.controlsFrame)
                .setBackgroundColor(CameraUtil.darkenColor(primaryColor));

        if (savedInstanceState != null) {
            mOutputUri = savedInstanceState.getString("output_uri");
        }
    }

    @Override
    public void onDestroyView()
    {
        super.onDestroyView();
        mButtonVideo = null;
        mButtonFacing = null;
        mRecordDuration = null;
    }

    @Override
    public void onResume()
    {
        super.onResume();
        if (mInterface != null && mInterface.hasLengthLimit()) {
            if (mInterface.countdownImmediately() || mInterface.getRecordingStart() > -1) {
                if (mInterface.getRecordingStart() == -1) {
                    mInterface.setRecordingStart(System.currentTimeMillis());
                }
                startCounter();
            } else {
                mRecordDuration.setText(String.format("-%s",
                        CameraUtil.getDurationString(mInterface.getLengthLimit())));
            }
        }
    }

    @SuppressWarnings ("deprecation")
    @Override
    public final void onAttach(Activity activity)
    {
        super.onAttach(activity);
        mInterface = (BaseCaptureInterface) activity;
    }

    @NonNull
    protected final File getOutputVideoFile()
    {
        return CameraUtil.makeTempFile(getActivity(), getArguments().getString(
                com.bakkle.bakkle.AddItem.MaterialCamera.internal.CameraIntentKey.SAVE_DIR),
                ".mp4");
    }

    @NonNull
    protected final File getOutputImageFile()
    {
        return CameraUtil.makeTempFile(getActivity(), getArguments().getString(
                com.bakkle.bakkle.AddItem.MaterialCamera.internal.CameraIntentKey.SAVE_DIR),
                ".jpg");
    }

    public abstract void openCamera();

    public abstract void closeCamera();

    @Override
    public void onPause()
    {
        super.onPause();
        closeCamera();
        releaseRecorder();
        stopCounter();
    }

    @Override
    public final void onDetach()
    {
        super.onDetach();
        mInterface = null;
    }

    public final void startCounter()
    {
        if (mPositionHandler == null) {
            mPositionHandler = new Handler();
        } else {
            mPositionHandler.removeCallbacks(mPositionUpdater);
        }
        mPositionHandler.post(mPositionUpdater);
    }

    @com.bakkle.bakkle.AddItem.MaterialCamera.internal.BaseCaptureActivity.CameraPosition
    public final int getCurrentCameraPosition()
    {
        if (mInterface == null) {
            return com.bakkle.bakkle.AddItem.MaterialCamera.internal.BaseCaptureActivity.CAMERA_POSITION_UNKNOWN;
        }
        return mInterface.getCurrentCameraPosition();
    }

    public final int getCurrentCameraId()
    {
        if (mInterface.getCurrentCameraPosition() == com.bakkle.bakkle.AddItem.MaterialCamera.internal.BaseCaptureActivity.CAMERA_POSITION_BACK) {
            return (Integer) mInterface.getBackCamera();
        } else {
            return (Integer) mInterface.getFrontCamera();
        }
    }

    public final void stopCounter()
    {
        if (mPositionHandler != null) {
            mPositionHandler.removeCallbacks(mPositionUpdater);
            mPositionHandler = null;
        }
    }

    public final void releaseRecorder()
    {
        if (mMediaRecorder != null) {
            if (mIsRecording) {
                try {
                    mMediaRecorder.stop();
                } catch (Throwable t) {
                    //noinspection ResultOfMethodCallIgnored
                    new File(mOutputUri).delete();
                    t.printStackTrace();
                }
                mIsRecording = false;
            }
            mMediaRecorder.reset();
            mMediaRecorder.release();
            mMediaRecorder = null;
        }
    }

    public boolean startRecordingVideo()
    {
        if (mInterface != null && mInterface.hasLengthLimit() && !mInterface.countdownImmediately()) {
            // Countdown wasn't started in onResume, start it now
            if (mInterface.getRecordingStart() == -1) {
                mInterface.setRecordingStart(System.currentTimeMillis());
            }
            startCounter();
        }

        final int orientation = Degrees.getActivityOrientation(getActivity());
        //noinspection ResourceType
        getActivity().setRequestedOrientation(orientation);
        mInterface.setDidRecord(true);
        return true;
    }

    public void takePicture()
    {
        final int orientation = Degrees.getActivityOrientation(getActivity());
        getActivity().setRequestedOrientation(orientation);

    }

    public void stopRecordingVideo(boolean reachedZero)
    {
        getActivity().setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED);
    }

    @Override
    public final void onSaveInstanceState(Bundle outState)
    {
        super.onSaveInstanceState(outState);
        outState.putString("output_uri", mOutputUri);
    }

    @Override
    public final String getOutputUri()
    {
        return mOutputUri;
    }

    protected final void throwError(Exception e)
    {
        Activity act = getActivity();
        if (act != null) {
            e.printStackTrace();
            act.setResult(RESULT_CANCELED, new Intent().putExtra(MaterialCamera.ERROR_EXTRA, e));
            act.finish();
        }
    }

    @Override
    public void onClick(View view)
    {
        if (view.getId() == R.id.facing) {
            mInterface.toggleCameraPosition();
            mButtonFacing.setImageResource(
                    mInterface.getCurrentCameraPosition() == com.bakkle.bakkle.AddItem.MaterialCamera.internal.BaseCaptureActivity.CAMERA_POSITION_BACK ? R.drawable.mcam_camera_front : R.drawable.mcam_camera_rear);
            closeCamera();
            openCamera();
        } else if (view.getId() == R.id.video) {
            if (mIsRecording) {
                stopRecordingVideo(false);
                mIsRecording = false;
            } else {
                if (getArguments().getBoolean(
                        com.bakkle.bakkle.AddItem.MaterialCamera.internal.CameraIntentKey.SHOW_PORTRAIT_WARNING,
                        true) && Degrees.isPortrait(getActivity())) {
                    new MaterialDialog.Builder(getActivity()).title(R.string.mcam_portrait)
                            .content(R.string.mcam_portrait_warning)
                            .positiveText(R.string.mcam_yes)
                            .negativeText(android.R.string.cancel)
                            .onPositive(new MaterialDialog.SingleButtonCallback()
                            {
                                @Override
                                public void onClick(@NonNull MaterialDialog materialDialog,
                                                    @NonNull DialogAction dialogAction)
                                {
                                    mIsRecording = startRecordingVideo();
                                }
                            })
                            .show();
                } else {
                    mIsRecording = startRecordingVideo();
                }
            }
        } else if (view.getId() == R.id.picture) {
            takePicture();
        }
    }
}