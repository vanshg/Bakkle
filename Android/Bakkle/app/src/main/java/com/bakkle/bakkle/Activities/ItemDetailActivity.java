package com.bakkle.bakkle.Activities;

import android.content.Intent;
import android.content.SharedPreferences;
import android.media.ThumbnailUtils;
import android.os.Bundle;
import android.os.Environment;
import android.preference.PreferenceManager;
import android.provider.MediaStore;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.widget.ImageView;
import android.widget.RelativeLayout;
import android.widget.TextView;

import com.bakkle.bakkle.Helpers.ServerCalls;
import com.bakkle.bakkle.R;
import com.bumptech.glide.Glide;
import com.koushikdutta.ion.Ion;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;


public class ItemDetailActivity extends AppCompatActivity
{

//    private Toolbar toolbar;
    private ArrayList<ImageView> productPictureViews = new ArrayList<>();
    String parent;
    String title;
    String price;
    String description;
    String sellerImageUrl;
    ArrayList<String> imageURLs;
    String seller;
    String distance;
    String pk;
    boolean garage;
    ServerCalls serverCalls;
    SharedPreferences preferences;

    @Override
    protected void onCreate(Bundle savedInstanceState)
    {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_item_detail);
        //      toolbar_home = (Toolbar) findViewById(R.id.toolbar_home);
//        setSupportActionBar(toolbar_home);

        Intent intent = getIntent();
        serverCalls = new ServerCalls(this);
        preferences = PreferenceManager.getDefaultSharedPreferences(this);
        garage = intent.getBooleanExtra("garage", false);
        title = intent.getStringExtra("title");
        price = intent.getStringExtra("price");
        description = intent.getStringExtra("description");
        seller = intent.getStringExtra("seller");
        distance = intent.getStringExtra("distance");
        pk = intent.getStringExtra("pk");
        sellerImageUrl = intent.getStringExtra("sellerImageUrl");
        imageURLs = intent.getStringArrayListExtra("imageURLs");
        parent = intent.getStringExtra("parent");
        if (imageURLs != null) {
            for (String url : imageURLs) {
                Log.v("test", "url is " + url);
                loadPictureIntoView(url);
            }
        }
        else {
            Log.v("test", "imageURLs was null");
        }

        ((TextView) findViewById(R.id.seller)).setText(seller);
        ((TextView) findViewById(R.id.title)).setText(title);
        ((TextView) findViewById(R.id.description)).setText(description);
        ((TextView) findViewById(R.id.distance)).setText(distance);
        ((TextView) findViewById(R.id.price)).setText(price);
        if (garage) {
            findViewById(R.id.wantButton).setVisibility(View.GONE);
        }

        Glide.with(this)
                .load(sellerImageUrl)
                .into((ImageView) findViewById(R.id.sellerImage));
    }


    @Override
    public boolean onCreateOptionsMenu(Menu menu)
    {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu_item_detail, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item)
    {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        int id = item.getItemId();

        //noinspection SimplifiableIfStatement
        if (id == R.id.action_settings) {
            return true;
        }

        return super.onOptionsItemSelected(item);
    }

    public void loadPictureIntoView(String url)
    {
        RelativeLayout relativeLayout = (RelativeLayout) findViewById(R.id.imageCollection);
        ImageView imageView = new ImageView(this);
        imageView.setId(productPictureViews.size() + 1);

        RelativeLayout.LayoutParams layoutParams = new RelativeLayout.LayoutParams(
                RelativeLayout.LayoutParams.MATCH_PARENT,
                RelativeLayout.LayoutParams.MATCH_PARENT);
        if (imageView.getId() != 1) {
            ImageView previous = productPictureViews.get(productPictureViews.size() - 1);
            layoutParams.addRule(RelativeLayout.RIGHT_OF, previous.getId());
            imageView.setPadding(10, 0, 0, 0);
        }

        imageView.setLayoutParams(layoutParams);
        imageView.setAdjustViewBounds(true);
        imageView.setScaleType(ImageView.ScaleType.FIT_CENTER);

        relativeLayout.addView(imageView);

        if (!url.endsWith("mp4")) {
            Glide.with(this)
                    .load(url)
                    .fitCenter()
                    .crossFade()
                    .placeholder(R.drawable.loading)
                    .into(imageView);
        }
        else { //TODO: Download and display video
            try {

            }
            catch (Exception e){}
        }


        productPictureViews.add(imageView);
    }

    public void markWant(View view)
    {
        serverCalls.markItem("want",
                preferences.getString("auth_token", "0"),
                preferences.getString("uuid", "0"),
                pk,
                "42");
        Intent intent = new Intent();
        intent.putExtra("markWant", true);
        if(parent.equals("feed"))
        {
            setResult(1, intent);
        }
        finish();
    }

    public void end(View view)
    {
        finish();
    }
}
