package com.bakkle.bakkle.Profile;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.content.Context;
import android.os.Bundle;
import android.support.v4.app.Fragment;
import android.text.TextUtils;
import android.util.Log;
import android.view.KeyEvent;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import com.android.volley.Response;
import com.bakkle.bakkle.API;
import com.bakkle.bakkle.Constants;
import com.bakkle.bakkle.Prefs;
import com.bakkle.bakkle.R;

import org.json.JSONException;
import org.json.JSONObject;

/**
 * A simple {@link Fragment} subclass.
 */
public class LoginFragment extends Fragment
{
    RegisterActivity activity;
    boolean started = false;
    private EditText emailEditText;
    private EditText passwordEditText;
    private View     progressView;
    private View     loginFormView;
    private String   password;

    public static LoginFragment newInstance()
    {
        return new LoginFragment();
    }

    public LoginFragment()
    {
        // Required empty public constructor
    }

    @Override
    public void onAttach(Context context)
    {
        super.onAttach(context);
        if (context instanceof RegisterActivity) {
            activity = (RegisterActivity) context;
        }
    }

    @Override
    public void onCreate(Bundle savedInstanceState)
    {
        super.onCreate(savedInstanceState);
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState)
    {
        // Inflate the layout for this fragment
        View view = inflater.inflate(R.layout.fragment_login, container, false);

        if (activity.getSupportActionBar() != null) {
            activity.getSupportActionBar().show();
            activity.getSupportActionBar().setTitle(getString(R.string.action_sign_in_short));
            activity.getSupportActionBar().setDisplayHomeAsUpEnabled(true);
        }

        loginFormView = view.findViewById(R.id.login_form);
        progressView = view.findViewById(R.id.login_progress);
        emailEditText = (EditText) view.findViewById(R.id.email);
        passwordEditText = (EditText) view.findViewById(R.id.password);
        Button signInButton = (Button) view.findViewById(R.id.email_sign_in_button);

        passwordEditText.setOnEditorActionListener(new TextView.OnEditorActionListener()
        {
            @Override
            public boolean onEditorAction(TextView textView, int id, KeyEvent keyEvent)
            {
                if (id == R.id.login || id == EditorInfo.IME_NULL) {
                    attemptLogin();
                    return true;
                }
                return false;
            }
        });

        signInButton.setOnClickListener(new View.OnClickListener()
        {
            @Override
            public void onClick(View view)
            {
                attemptLogin();
            }
        });

        return view;
    }

    private void attemptLogin()
    {
        if (started) {
            return;
        }
        started = true;

        // Reset errors.
        emailEditText.setError(null);
        passwordEditText.setError(null);

        // Store values at the time of the login attempt.
        String email = emailEditText.getText().toString();
        password = passwordEditText.getText().toString();

        boolean cancel = false;
        View focusView = null;

        // Check for a valid password, if the user entered one.
        if (TextUtils.isEmpty(password)) {
            passwordEditText.setError(getString(R.string.error_invalid_password));
            focusView = passwordEditText;
            cancel = true;
        }

        // Check for a valid email address.
        if (TextUtils.isEmpty(email)) {
            emailEditText.setError(getString(R.string.error_field_required));
            focusView = emailEditText;
            cancel = true;
        }

        if (cancel) {
            // There was an error; don't attempt login and focus the first
            // form field with an error.
            focusView.requestFocus();
        } else {
            // Show a progress spinner, and kick off a background task to
            // perform the user login attempt.
            showProgress(true);
            API.getInstance().getEmailUserId(email, new EmailIdListener());
            //TODO: How do you submit the password to the server?
        }
    }

    private void showProgress(final boolean show)
    {
        int shortAnimTime = getResources().getInteger(android.R.integer.config_shortAnimTime);

        loginFormView.setVisibility(show ? View.GONE : View.VISIBLE);
        loginFormView.animate()
                .setDuration(shortAnimTime)
                .alpha(show ? 0 : 1)
                .setListener(new AnimatorListenerAdapter()
                {
                    @Override
                    public void onAnimationEnd(Animator animation)
                    {
                        loginFormView.setVisibility(show ? View.GONE : View.VISIBLE);
                    }
                });

        progressView.setVisibility(show ? View.VISIBLE : View.GONE);
        progressView.animate()
                .setDuration(shortAnimTime)
                .alpha(show ? 1 : 0)
                .setListener(new AnimatorListenerAdapter()
                {
                    @Override
                    public void onAnimationEnd(Animator animation)
                    {
                        progressView.setVisibility(show ? View.VISIBLE : View.GONE);
                    }
                });
    }

    private class EmailIdListener implements Response.Listener<JSONObject>
    {
//        private String name;
//
//        public EmailIdListener(String name)
//        {
//            this.name = name;
//        }

        @Override
        public void onResponse(JSONObject response)
        {
            try {
                if (response.has("status") && response.getInt("status") == 1) {
                    Prefs prefs = Prefs.getInstance(getContext());
                    prefs.setUserId(response.getString("userid"));
//                    prefs.setUsername(name);
//                    prefs.setName(name);
//                    String[] split = name.split(" ");
//                    if (split.length >= 2) {
//                        prefs.setFirstName(split[0]);
//                        prefs.setLastName(split[split.length - 1]);
//                    } else {
//                        prefs.setFirstName(name);
//                        prefs.setLastName("");
//                    }
                    API.getInstance().authenticatePassword(password, new AuthenticateListener());
                } else {
                    Toast.makeText(getContext(), "There was error signing in", Toast.LENGTH_SHORT)
                            .show();
                    started = false;
                }
            } catch (JSONException e) {
                Toast.makeText(getContext(), "There was error signing in", Toast.LENGTH_SHORT)
                        .show();
                started = false;
            }
        }

        public class AuthenticateListener implements Response.Listener<JSONObject>
        {
            @Override
            public void onResponse(JSONObject response)
            {
                Log.v("LoginFragment", response.toString());
                try {
                    if (response.getInt("success") == 1) {
                        API.getInstance().registerFacebook(new LoginListener());
                    }
                } catch (JSONException e) {
                    Toast.makeText(getContext(), "There was error signing in", Toast.LENGTH_SHORT)
                            .show();
                }
            }
        }

        private class LoginListener implements Response.Listener<JSONObject>
        {
            @Override
            public void onResponse(JSONObject response)
            {
                try {
                    Prefs prefs = Prefs.getInstance(getContext());
                    prefs.setAuthToken(response.getString("auth_token"));
                    prefs.setAuthenticated(true);
                    prefs.setLoggedIn(true);
                    prefs.setGuest(false);

                    getActivity().setResult(Constants.REUSLT_CODE_OK);
                    getActivity().finish();
                } catch (JSONException e) {
                    Toast.makeText(getContext(), "There was error signing in", Toast.LENGTH_SHORT)
                            .show();
                }
            }
        }
    }
}
