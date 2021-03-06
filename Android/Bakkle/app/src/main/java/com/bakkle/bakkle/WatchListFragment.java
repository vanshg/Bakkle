package com.bakkle.bakkle;

import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.support.design.widget.Snackbar;
import android.support.v4.app.Fragment;
import android.support.v4.widget.SwipeRefreshLayout;
import android.support.v7.widget.LinearLayoutManager;
import android.support.v7.widget.RecyclerView;
import android.support.v7.widget.helper.ItemTouchHelper;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import android.widget.Toast;

import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.bakkle.bakkle.Models.FeedItem;
import com.bakkle.bakkle.Models.Person;
import com.bakkle.bakkle.Profile.RegisterActivity;
import com.bakkle.bakkle.Views.DividerItemDecoration;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

public class WatchListFragment extends Fragment
{
    RecyclerView       recyclerView;
    SwipeRefreshLayout listContainer;
    List<FeedItem>     items;
    WatchListAdapter   adapter;
    TextView           emptyListTextView;

    public WatchListFragment()
    {
    }

    public static WatchListFragment newInstance()
    {
        return new WatchListFragment();
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
        final View view = inflater.inflate(R.layout.recycler_view, container, false);
        emptyListTextView = (TextView) view.findViewById(R.id.empty_list_message);
        emptyListTextView.setText(R.string.watchlist_empty_message);

        ((MainActivity) getActivity()).getSupportActionBar().setTitle("Watch List");

        ItemTouchHelper.SimpleCallback simpleItemTouchCallback = new ItemTouchHelper.SimpleCallback(
                0, ItemTouchHelper.LEFT)
        {

            @Override
            public boolean onMove(RecyclerView recyclerView, RecyclerView.ViewHolder viewHolder,
                                  RecyclerView.ViewHolder target)
            {
                return false;
            }

            @Override
            public void onSwiped(RecyclerView.ViewHolder viewHolder, int direction)
            {
                final int position = viewHolder.getAdapterPosition();
                final FeedItem deletedItem = items.remove(position);
                adapter.notifyItemRemoved(position);

                final Snackbar snackbar = Snackbar.make(view,
                        deletedItem.getTitle().concat(" has been deleted from Watchlist"),
                        Snackbar.LENGTH_LONG).setAction("Undo", new View.OnClickListener()
                {
                    @Override
                    public void onClick(View v)
                    {
                        items.add(position, deletedItem);
                        adapter.notifyItemInserted(position);
                    }
                }).setCallback(new Snackbar.Callback()
                {
                    @Override
                    public void onDismissed(Snackbar snackbar, int event)
                    {
                        if (event == DISMISS_EVENT_ACTION) {
                            Snackbar.make(view,
                                    deletedItem.getTitle().concat(" has been restored to Watchlist"),
                                    Snackbar.LENGTH_SHORT).show();
                            return; //If an action was used to dismiss, the user wants to undo the deletion, so we do not need to continue
                        }
                        API.getInstance(getContext())
                                .markItem(Constants.MARK_NOPE, deletedItem.getPk(), "42");
                    }
                });
                snackbar.show();
            }
        };

        ItemTouchHelper itemTouchHelper = new ItemTouchHelper(simpleItemTouchCallback);

        recyclerView = (RecyclerView) view.findViewById(R.id.list);
        listContainer = (SwipeRefreshLayout) view.findViewById(R.id.listContainer);

        listContainer.setColorSchemeResources(R.color.colorPrimary, R.color.colorNope,
                R.color.colorHoldBlue);

        listContainer.setOnRefreshListener(new SwipeRefreshLayout.OnRefreshListener()
        {
            @Override
            public void onRefresh()
            {
                refreshWatchList();
            }
        });

        recyclerView.addItemDecoration(
                new DividerItemDecoration(getContext(), DividerItemDecoration.VERTICAL_LIST));

        recyclerView.setLayoutManager(new LinearLayoutManager(getContext()));
        itemTouchHelper.attachToRecyclerView(recyclerView);

        refreshWatchList();

        return view;
    }

    public void refreshWatchList()
    {
        API.getInstance(getContext())
                .getWatchList(new WatchListListener(), new WatchListErrorListener());
    }

    @Override
    public void onAttach(Context context)
    {
        super.onAttach(context);
    }

    @Override
    public void onDetach()
    {
        super.onDetach();
    }

    // Format of JSON:
    /*
    "status": ,
    "holding_pattern": [
        {
            "view_time": "2015-12-07 01:31:08 ",
            "status": "Hold",
            "confirmed_price": "0.00",
            "item": {
                "status": "Active",
                "description": "WORDS TO DESCRIBE ITEM",
                "tags": "",
                "price": "0.00",
                "image_urls": [
                    "https://s3-us-west-2.amazonaws.com/com.bakkle.prod/com.bakkle.prod_223_df2b464a179a24ff6574e752a387f578.jpg",
                    "https://s3-us-west-2.amazonaws.com/com.bakkle.prod/com.bakkle.prod_223_c7e4940f34cee924a6cf2a242d5de5b4.mp4"
                ],
                "post_date": "2015-12-03 16:52:26 ",
                "title": "Golden  phone",
                "seller": {
                    "avatar_image_url": "https://app.bakkle.com/img/default_profile.png",
                    "buyer_rating": null,
                    "display_name": "Niraj",
                    "description": null,
                    "facebook_id": "533675fb606daeed071c7b447a8779bf",
                    "pk": 223,
                    "flavor": 1,
                    "user_location": "40.6,-74.49",
                    "seller_rating": null
                },
                "location": "40.73,-74.53",
                "pk": 3278,
                "method": "Pick-up"
            },
            "buyer": {
                "avatar_image_url": "http://graph.facebook.com/953976251314552/picture",
                "buyer_rating": null,
                "display_name": "Vansh Gandhi",
                "description": "Testing description on Android!",
                "facebook_id": "953976251314552",
                "pk": 11,
                "flavor": 1,
                "user_location": "37.65,-121.9",
                "seller_rating": null
            },
            "pk": 26753,
            "accepted_sale_price": false,
            "sale": null,
            "view_duration": "42.00"
        }, etc
     */

    public List<FeedItem> processJson(JSONObject json) throws JSONException
    {
        if (json.getInt("status") != 1) {
            return null;
        }
        JSONArray jsonArray = json.getJSONArray("holding_pattern");
        int length = jsonArray.length();
        List<FeedItem> items = new ArrayList<>(length);
        for (int i = 0; i < length; i++) {
            JSONObject item = jsonArray.getJSONObject(i)
                    .getJSONObject("item"); //TODO: Capture rest of JSON information returned
            JSONObject sellerJson = item.getJSONObject("seller");
            JSONArray image_urlsJson = item.getJSONArray("image_urls");

            FeedItem feedItem = new FeedItem();
            Person seller = new Person();
            String[] image_urls = new String[image_urlsJson.length()];

            for (int k = 0; k < image_urls.length; k++) {
                image_urls[k] = image_urlsJson.getString(k);
            }

            seller.setDisplay_name(sellerJson.getString("display_name"));
            seller.setDescription(sellerJson.getString("description"));
            seller.setFacebook_id(sellerJson.getString("facebook_id"));
            seller.setAvatar_image_url(seller.getFacebook_id()
                    .matches(
                            "[0-9]+") ? "https://graph.facebook.com/" + seller.getFacebook_id() + "/picture?type=normal" : null);
            seller.setPk(sellerJson.getInt("pk"));
            seller.setFlavor(sellerJson.getInt("flavor"));
            seller.setUser_location(sellerJson.getString("user_location"));

            feedItem.setStatus(item.getString("status"));
            feedItem.setDescription(item.getString("description"));
            feedItem.setPrice(item.getString("price"));
            feedItem.setPost_date(item.getString("post_date"));
            feedItem.setTitle(item.getString("title"));
            feedItem.setLocation(item.getString("location"));
            feedItem.setPk(item.getInt("pk"));
            feedItem.setMethod(item.getString("method"));
            feedItem.setImage_urls(image_urls);
            feedItem.setSeller(seller);

            items.add(feedItem);
        }
        return items;
    }

    private class WatchListListener implements Response.Listener<JSONObject>
    {
        @Override
        public void onResponse(JSONObject response)
        {
            try {
                items = processJson(response);
                if (items.size() == 0) {
                    emptyListTextView.setVisibility(View.VISIBLE);
                    listContainer.setVisibility(View.GONE);
                } else {
                    emptyListTextView.setVisibility(View.GONE);
                    listContainer.setVisibility(View.VISIBLE);
                }
                adapter = new WatchListAdapter(items, getActivity(), WatchListFragment.this);
                recyclerView.setAdapter(adapter);
                listContainer.setRefreshing(false);
            } catch (JSONException e) {
                Toast.makeText(getContext(), "There was error retrieving the Watch List",
                        Toast.LENGTH_SHORT).show();
                showError();
            }
        }
    }

    @Override
    public void onActivityResult(int requestCode, int resultCode, Intent data)
    {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == Constants.REQUEST_CODE_VIEW_ITEM) {
            if (resultCode == Constants.RESULT_CODE_NOPE) {
                API.getInstance(getContext())
                        .markItem(Constants.MARK_NOPE, data.getIntExtra(Constants.PK, -1), "42");
                int position = data.getIntExtra(Constants.POSITION, -1);
                items.remove(position);
                adapter.notifyItemRemoved(position);
            } else if (resultCode == Constants.RESULT_CODE_WANT) {
                if (Prefs.getInstance(getContext()).isGuest()) {
                    Intent intent = new Intent(getContext(), RegisterActivity.class);
                    startActivityForResult(intent, Constants.REQUEST_CODE_MARK_ITEM);
                } else {
                    API.getInstance(getContext())
                            .markItem(Constants.MARK_WANT, data.getIntExtra(Constants.PK, -1),
                                    "42");
                    int position = data.getIntExtra(Constants.POSITION, -1);
                    items.remove(position);
                    adapter.notifyItemRemoved(position);
                }
            }
        } else if (requestCode == Constants.REQUEST_CODE_MARK_ITEM) {
            if (resultCode == Constants.REUSLT_CODE_OK) {
                API.getInstance(getContext())
                        .markItem(Constants.MARK_WANT, data.getIntExtra(Constants.PK, -1), "42");
            }
        }
    }

    private void showError()
    {
        //TODO: Move showError() in FeedFragment to MainActivity, so that it can be used by any fragment
    }

    private class WatchListErrorListener implements Response.ErrorListener
    {

        @Override
        public void onErrorResponse(VolleyError error)
        {
            Toast.makeText(getContext(), "There was error retrieving the Watch List",
                    Toast.LENGTH_SHORT).show();
            showError();
        }
    }
}
