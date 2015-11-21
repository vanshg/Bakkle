package com.bakkle.bakkle.Activities;

import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.location.Location;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.provider.Settings;
import android.support.v4.app.NavUtils;
import android.support.v7.app.AlertDialog;
import android.support.v7.app.AppCompatActivity;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.View.OnClickListener;

import com.bakkle.bakkle.Helpers.Constants;
import com.bakkle.bakkle.R;
import com.facebook.AccessToken;
import com.facebook.AccessTokenTracker;
import com.facebook.CallbackManager;
import com.facebook.FacebookCallback;
import com.facebook.FacebookException;
import com.facebook.FacebookSdk;
import com.facebook.Profile;
import com.facebook.ProfileTracker;
import com.facebook.login.LoginManager;
import com.facebook.login.LoginResult;
import com.facebook.login.widget.LoginButton;

import java.util.Arrays;

import io.nlopez.smartlocation.OnLocationUpdatedListener;
import io.nlopez.smartlocation.SmartLocation;


public class LoginActivity extends AppCompatActivity implements OnClickListener
{

    private LoginButton loginButton;
    private CallbackManager callbackManager;
    private boolean isResumed = false;
    private AccessTokenTracker accessTokenTracker;
    AlertDialog.Builder builder = null;
    AlertDialog dialog = null;
    SharedPreferences preferences;
    SharedPreferences.Editor editor;


    @Override
    protected void onCreate(Bundle savedInstanceState)
    {
        super.onCreate(savedInstanceState);
        callbackManager = CallbackManager.Factory.create();
        FacebookSdk.sdkInitialize(this);
        preferences = PreferenceManager.getDefaultSharedPreferences(this);
        setContentView(R.layout.activity_login);


        if (!SmartLocation.with(this).location().state().locationServicesEnabled()) {
            builder = new AlertDialog.Builder(this);
            builder.setTitle("GPS not found");  // GPS not found
            builder.setMessage("In order for Bakkle to function properly, Location Services need to be enabled. Would like to enable them now?"); // Want to enable?
            builder.setPositiveButton("Yes", new DialogInterface.OnClickListener()
            {
                public void onClick(DialogInterface dialogInterface, int i)
                {
                    startActivity(new Intent(android.provider.Settings.ACTION_LOCATION_SOURCE_SETTINGS));
                }
            });
            builder.setNegativeButton("Not right now", null);
            dialog = builder.create();
            dialog.show();
        }
        else {
            SmartLocation.with(this).location()
                    .oneFix()
                    .start(new OnLocationUpdatedListener()
                    {
                        @Override
                        public void onLocationUpdated(Location location)
                        {
                            editor.putString(Constants.LOCATION, location.getLatitude() + "," + location.getLongitude());
                            editor.putString(Constants.LATITUDE, String.valueOf(location.getLatitude()));
                            editor.putString(Constants.LONGITUDE, String.valueOf(location.getLongitude()));
                            editor.apply();
                        }
                    });


            if (preferences.getBoolean(Constants.LOGGED_IN, false)) {

                Intent intent = new Intent(this, MainActivity.class);
                startActivity(intent);
                //SmartLocation.with(this).location().stop();
                finish();
            }

            editor = preferences.edit();
            editor.putString(Constants.UUID, Settings.Secure.getString(getContentResolver(), Settings.Secure.ANDROID_ID));
            editor.apply();

            Log.v("uuid is", preferences.getString(Constants.UUID, "0"));
            LoginManager.getInstance().registerCallback(callbackManager, new FacebookCallback<LoginResult>()
            {
                private ProfileTracker mProfileTracker;

                @Override
                public void onSuccess(LoginResult loginResult)
                {
                    AccessToken token = loginResult.getAccessToken();
                    mProfileTracker = new ProfileTracker()
                    {
                        @Override
                        protected void onCurrentProfileChanged(Profile oldProfile, Profile currentProfile)
                        {
                            Profile.setCurrentProfile(currentProfile);
                            mProfileTracker.stopTracking();
                        }
                    };

                    mProfileTracker.startTracking();

                    if (token != null) {
                        editor.putBoolean("LoggedIn", true);
                        editor.apply();
                        Intent intent = new Intent(getApplicationContext(), MainActivity.class);
                        startActivity(intent);
                        finish();
                    }


                }

                @Override
                public void onCancel()
                {
                    System.out.println("Facebook Canceled");
                }

                @Override
                public void onError(FacebookException e)
                {
                    System.out.println(e.getMessage());
                }
            });

            // Set up custom Action Bar and enable up navigation
//        getActionBar().setDisplayOptions(ActionBar.DISPLAY_SHOW_CUSTOM);
//        getActionBar().setCustomView(R.layout.action_bar_title);
//        getActionBar().setDisplayHomeAsUpEnabled(false);
//        getActionBar().setDisplayShowHomeEnabled(false);
//        getActionBar().setHomeButtonEnabled(false);

//        ((TextView)findViewById(R.id.action_bar_title)).setText(R.string.title_activity_sign_in);
//        ((ImageButton)findViewById(R.id.action_bar_right)).setVisibility(View.INVISIBLE);
//        ((ImageButton) findViewById(R.id.action_bar_home)).setImageResource(R.drawable.ic_action_cancel);
//        ((ImageButton) findViewById(R.id.action_bar_home)).setOnClickListener(this);

            // Add on click listeners to buttons
//        ((Button)findViewById(R.id.btnSignIn)).setOnClickListener(this);
            ((LoginButton) findViewById(R.id.btnSignInFacebook)).setOnClickListener(this);
        }
    }

    @Override
    public void onResume()
    {
        super.onResume();
        if(builder != null && dialog != null)
            dialog.dismiss();
        if (!SmartLocation.with(this).location().state().locationServicesEnabled()) {
            builder = new AlertDialog.Builder(this);
            builder.setTitle("GPS not found");  // GPS not found
            builder.setMessage("In order for Bakkle to function properly, Location Services need to be enabled. Would like to enable them now?"); // Want to enable?
            builder.setPositiveButton("Yes", new DialogInterface.OnClickListener()
            {
                public void onClick(DialogInterface dialogInterface, int i)
                {
                    startActivity(new Intent(android.provider.Settings.ACTION_LOCATION_SOURCE_SETTINGS));
                }
            });
            builder.setNegativeButton("Not right now", null);
            builder.create().show();
        }
        else {
            SmartLocation.with(this).location()
                    .oneFix()
                    .start(new OnLocationUpdatedListener()
                    {
                        @Override
                        public void onLocationUpdated(Location location)
                        {
                            editor.putString(Constants.LOCATION, location.getLatitude() + "," + location.getLongitude());
                            editor.putString(Constants.LATITUDE, String.valueOf(location.getLatitude()));
                            editor.putString(Constants.LONGITUDE, String.valueOf(location.getLongitude()));
                            editor.apply();
                        }
                    });


            if (preferences.getBoolean(Constants.LOGGED_IN, false)) {

                Intent intent = new Intent(this, MainActivity.class);
                startActivity(intent);
                //SmartLocation.with(this).location().stop();
                finish();
            }

            editor = preferences.edit();
            editor.putString(Constants.UUID, Settings.Secure.getString(getContentResolver(), Settings.Secure.ANDROID_ID));
            editor.apply();

            Log.v("uuid is", preferences.getString(Constants.UUID, "0"));
            LoginManager.getInstance().registerCallback(callbackManager, new FacebookCallback<LoginResult>()
            {
                private ProfileTracker mProfileTracker;

                @Override
                public void onSuccess(LoginResult loginResult)
                {
                    AccessToken token = loginResult.getAccessToken();
                    mProfileTracker = new ProfileTracker()
                    {
                        @Override
                        protected void onCurrentProfileChanged(Profile oldProfile, Profile currentProfile)
                        {
                            Profile.setCurrentProfile(currentProfile);
                            mProfileTracker.stopTracking();
                        }
                    };

                    mProfileTracker.startTracking();

                    if (token != null) {
                        editor.putBoolean("LoggedIn", true);
                        editor.apply();
                        Intent intent = new Intent(getApplicationContext(), MainActivity.class);
                        startActivity(intent);
                        finish();
                    }


                }

                @Override
                public void onCancel()
                {
                    System.out.println("Facebook Canceled");
                }

                @Override
                public void onError(FacebookException e)
                {
                    System.out.println(e.getMessage());
                }
            });

            // Set up custom Action Bar and enable up navigation
//        getActionBar().setDisplayOptions(ActionBar.DISPLAY_SHOW_CUSTOM);
//        getActionBar().setCustomView(R.layout.action_bar_title);
//        getActionBar().setDisplayHomeAsUpEnabled(false);
//        getActionBar().setDisplayShowHomeEnabled(false);
//        getActionBar().setHomeButtonEnabled(false);

//        ((TextView)findViewById(R.id.action_bar_title)).setText(R.string.title_activity_sign_in);
//        ((ImageButton)findViewById(R.id.action_bar_right)).setVisibility(View.INVISIBLE);
//        ((ImageButton) findViewById(R.id.action_bar_home)).setImageResource(R.drawable.ic_action_cancel);
//        ((ImageButton) findViewById(R.id.action_bar_home)).setOnClickListener(this);

            // Add on click listeners to buttons
//        ((Button)findViewById(R.id.btnSignIn)).setOnClickListener(this);
            ((LoginButton) findViewById(R.id.btnSignInFacebook)).setOnClickListener(this);
        }
    }


    @Override
    public boolean onCreateOptionsMenu(Menu menu)
    {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu_sign_in, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item)
    {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        return super.onOptionsItemSelected(item);
    }

    @Override
    public void onActivityResult(int requestCode, int resultCode, Intent data)
    {
        super.onActivityResult(requestCode, resultCode, data);
        callbackManager.onActivityResult(requestCode, resultCode, data);
    }

    @Override
    public void onClick(View v)
    {
        int id = v.getId();
        switch (id) {
            case R.id.btnSignIn:
                // TODO: Implement Sign in Code
                Intent homeIntent = new Intent(this, MainActivity.class);
                startActivity(homeIntent);
                finish();
                break;
            case R.id.btnSignInFacebook:
                if (preferences.getBoolean(Constants.LOGGED_IN, false)) {
                    LoginManager.getInstance().logOut();
                    editor.putBoolean(Constants.LOGGED_IN, false);
                    editor.apply();
                }
                else {
                    LoginManager.getInstance().logInWithReadPermissions(this, Arrays.asList
                            ("public_profile", "email", "user_friends"));
                    LoginManager.getInstance().logInWithPublishPermissions(
                            this, Arrays.asList("publish_actions"));
                    editor.putBoolean(Constants.LOGGED_IN, true);
                    editor.putBoolean(Constants.NEW_USER, true);
                    editor.apply();
                }
                break;
            case R.id.action_bar_home:
                NavUtils.navigateUpFromSameTask(this);
                break;
        }
    }


    @Override
    public void onBackPressed()
    {
        //startActivity(new Intent(this, SignupActivity.class));
        finish();
    }

}
