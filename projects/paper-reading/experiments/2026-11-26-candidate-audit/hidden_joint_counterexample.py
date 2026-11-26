"""Original finite-state identifiability example, not a network simulation."""
import json

models={'shared':{(0,0):0.5,(1,1):0.5},'exclusive':{(0,1):0.5,(1,0):0.5}}
out={}
for name,states in models.items():
    old={f'action={a},ack={y}':sum(p*0.5 for s,p in states.items() if s[a]==y) for a in [0,1] for y in [0,1]}
    new=sum(p for s,p in states.items() if all(s))
    out[name]={'old_joint_action_ack_distribution':old,'new_both_links_success_probability':new}
out['old_observation_total_variation']=0.5*sum(abs(out['shared']['old_joint_action_ack_distribution'][k]-out['exclusive']['old_joint_action_ack_distribution'][k]) for k in out['shared']['old_joint_action_ack_distribution'])
out['assumptions']=['hidden two-bit state is independently reset each epoch','old policy samples exactly one of two actions per epoch, uniformly','new policy tests both links within one fixed-state epoch','no common-busy or other side observation is available']
print(json.dumps(out,indent=2))
