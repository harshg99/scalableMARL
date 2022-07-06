from asyncio.proactor_events import _ProactorDuplexPipeTransport
import pdb, argparse, os, datetime, json, pickle
import torch
import torch.nn as nn

import gym
from gym import wrappers

from algos.maTT.dql import doubleQlearning
import algos.maTT.core as core

import envs

__author__ = 'Christopher D Hsu'
__copyright__ = ''
__credits__ = ['Christopher D Hsu']
__license__ = ''
__version__ = '0.0.1'
__maintainer__ = 'Christopher D Hsu'
__email__ = 'chsu8@seas.upenn.edu'
__status__ = 'Dev'


os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

BASE_DIR = os.path.dirname('/'.join(str.split(os.path.realpath(__file__),'/')[:-2]))



## cleanRL
def parse_args():
    # fmt: off
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    #parser.add_argument("--exp-name", type=str, default=os.path.basename(__file__).rstrip(".py"),
    #    help="the name of this experiment")
    parser.add_argument("--seed", type=int, default=1,
        help="seed of the experiment")
    parser.add_argument("--torch-deterministic", type=lambda x: bool(strtobool(x)), default=True, nargs="?", const=True,
        help="if toggled, `torch.backends.cudnn.deterministic=False`")
    parser.add_argument("--cuda", type=lambda x: bool(strtobool(x)), default=True, nargs="?", const=True,
        help="if toggled, cuda will be enabled by default")
    parser.add_argument("--track", type=lambda x: bool(strtobool(x)), default=False, nargs="?", const=True,
        help="if toggled, this experiment will be tracked with Weights and Biases")
    parser.add_argument("--wandb-project-name", type=str, default="scalableMARL",
        help="the wandb's project name")
    parser.add_argument("--wandb-entity", type=str, default=None,
        help="the entity (team) of wandb's project")
    #parser.add_argument("--capture-video", type=lambda x: bool(strtobool(x)), default=False, nargs="?", const=True,
    #    help="weather to capture videos of the agent performances (check out `videos` folder)")

    # Algorithm specific arguments
    #parser.add_argument("--env-id", type=str, default="CartPole-v1",
    #    help="the id of the environment")
    parser.add_argument("--total_timesteps", type=int, default=2000000,
        help="total timesteps of the experiments")
    parser.add_argument("--learning_rate", type=float, default=2.5e-4,
        help="the learning rate of the optimizer")
    parser.add_argument("--num_envs", type=int, default=4,
        help="the number of parallel game environments")
    parser.add_argument("--num_steps", type=int, default=128,
        help="the number of steps to run in each environment per policy rollout")
    parser.add_argument("--anneal_lr", type=lambda x: bool(strtobool(x)), default=True, nargs="?", const=True,
        help="Toggle learning rate annealing for policy and value networks")
    parser.add_argument("--gae", type=lambda x: bool(strtobool(x)), default=True, nargs="?", const=True,
        help="Use GAE for advantage computation")
    parser.add_argument("--gamma", type=float, default=0.99,
        help="the discount factor gamma")
    parser.add_argument("--gae_lambda", type=float, default=0.95,
        help="the lambda for the general advantage estimation")
    parser.add_argument("--num_minibatches", type=int, default=4,
        help="the number of mini-batches")
    parser.add_argument("--update_epochs", type=int, default=4,
        help="the K epochs to update the policy")
    parser.add_argument("--norm_adv", type=lambda x: bool(strtobool(x)), default=True, nargs="?", const=True,
        help="Toggles advantages normalization")
    parser.add_argument("--clip_coef", type=float, default=0.2,
        help="the surrogate clipping coefficient")
    parser.add_argument("--clip_vloss", type=lambda x: bool(strtobool(x)), default=True, nargs="?", const=True,
        help="Toggles whether or not to use a clipped loss for the value function, as per the paper.")
    parser.add_argument("--ent_coef", type=float, default=0.01,
        help="coefficient of the entropy")
    parser.add_argument("--vf_coef", type=float, default=0.5,
        help="coefficient of the value function")
    parser.add_argument("--max_grad_norm", type=float, default=0.5,
        help="the maximum norm for the gradient clipping")
    parser.add_argument("--target_kl", type=float, default=None,
        help="the target KL divergence threshold")
    parser.add_argument('--one_network', action='store_true')
    parser.set_defaults(one_network=False)
    
    ## maTT
    
    parser.add_argument('--env', help='environment ID', default='setTracking-v1')
    parser.add_argument('--map', type=str, default="emptyMed")
    parser.add_argument('--nb_agents', type=int, default=4)
    parser.add_argument('--nb_targets', type=int, default=4)
    #parser.add_argument('--seed', help='RNG seed', type=int, default=0)
    parser.add_argument('--mode', choices=['train', 'test', 'test-behavior'], default='train')
    #parser.add_argument('--steps_per_epoch', type=int, default=25000)
    #parser.add_argument('--epochs', type=int, default=20)
    #parser.add_argument('--batch_size', type=int, default=256)
    #parser.add_argument('--alpha', type=float, default=0.4)
    #parser.add_argument('--gamma', type=float, default=.99)
    #parser.add_argument('--polyak', type=float, default=0.999) #tau in polyak averaging
    #parser.add_argument('--hiddens', type=int, default=128)
    #parser.add_argument('--learning_rate', type=float, default=0.001)
    #parser.add_argument('--learning_rate_period', type=float, default=0.7) #Back half portion with cosine lr schedule
    #parser.add_argument('--grad_clip', type=int, default=0.2)
    #parser.add_argument('--start_steps', type=int, default=20000)
    #parser.add_argument('--update_after', type=int, default=20000)
    #parser.add_argument('--num_eval_episodes', type=int, default=2) #During training
    #parser.add_argument('--replay_size', type=int, default=int(1e6))
    #parser.add_argument('--max_ep_len', type=int, default=200)
    #parser.add_argument('--checkpoint_freq', type=int, default=1)

    parser.add_argument('--record',type=int, default=0)
    parser.add_argument('--render', type=int, default=0)
    parser.add_argument('--nb_test_eps',type=int, default=50)
    parser.add_argument('--log_dir', type=str, default='./results/maTT')
    parser.add_argument('--log_fname', type=str, default='model.pt')
    parser.add_argument('--repeat', type=int, default=1)
    parser.add_argument('--eval_type', choices=['random', 'fixed_4', 
                                                'fixed_2', 'fixed_nb'], default='fixed_nb')

    parser.add_argument('--torch_threads', type=int, default=1)
    parser.add_argument('--amp', type=int, default=0)
    args = parser.parse_args()
    args.batch_size = int(args.num_envs * args.num_steps)
    args.minibatch_size = int(args.batch_size // args.num_minibatches)
    # fmt: on
    return args



def train(save_dir, args):
    run_name = save_dir.split(os.sep)[-1]
    assert os.path.exists(save_dir)
    env = envs.make(args.env,
                    'ma_target_tracking',
                    render=bool(args.render),
                    record=bool(args.record),
                    directory=save_dir,
                    map_name=args.map,
                    num_agents=args.nb_agents,
                    num_targets=args.nb_targets,
                    is_training=True,
                    num_envs=args.num_envs
                    )

    # Create env function
    # env_fn = lambda : env
    if args.one_network:
        from algos.maTT.decentralized_ppo_one_network import decentralized_ppo
        decentralized_ppo(env, args, run_name)
    else:
        from algos.maTT.decentralized_ppo import decentralized_ppo
        decentralized_ppo(env, args, run_name)

def test(args):
    from algos.maTT.evaluation import Test, load_pytorch_policy
    
    env = envs.make(args.env,
                    'ma_target_tracking',
                    render=bool(args.render),
                    record=bool(args.record),
                    directory=args.log_dir,
                    map_name=args.map,
                    num_agents=args.nb_agents,
                    num_targets=args.nb_targets,
                    is_training=False,
                    )    

    # Load saved policy
    model_kwargs = dict(dim_hidden=args.hiddens)
    model = core.DeepSetmodel(env.observation_space, env.action_space, **model_kwargs)
    policy = load_pytorch_policy(args.log_dir, args.log_fname, model)

    # Testing environment
    Eval = Test()
    Eval.test(args, env, policy)

def testbehavior(args):
    from algos.maTT.evaluation_behavior import TestBehavior, load_pytorch_policy
    import algos.maTT.core_behavior as core_behavior
    
    env = envs.make(args.env,
                    'ma_target_tracking',
                    render=bool(args.render),
                    record=bool(args.record),
                    directory=args.log_dir,
                    map_name=args.map,
                    num_agents=args.nb_agents,
                    num_targets=args.nb_targets,
                    is_training=False,
                    )    

    # Load saved policy
    model_kwargs = dict(dim_hidden=args.hiddens)
    model = core_behavior.DeepSetmodel(env.observation_space, env.action_space, **model_kwargs)
    policy = load_pytorch_policy(args.log_dir, args.log_fname, model)

    # Testing environment
    Eval = TestBehavior()
    Eval.test(args, env, policy)


if __name__ == '__main__':
    args = parse_args()
    if args.mode == 'train':
        date = datetime.datetime.now().strftime("%m%d%H%M")
        run_name = f"{args.env}__{args.seed}__{date}"
        save_dir = os.path.join(args.log_dir, run_name)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        else:
            ValueError("The directory already exists...", save_dir)

        notes = input("Any notes for this experiment? : ")
        f = open(os.path.join(save_dir, "notes.txt"), 'w')
        f.write(notes)
        f.close()

        seed = args.seed
        list_records = []
        for _ in range(args.repeat):
            print("===== TRAIN A TARGET TRACKING RL AGENT : SEED %d ====="%seed)
            results = train(save_dir, args)
            json.dump(vars(args), open(os.path.join(save_dir, 'learning_prop.json'), 'w'))
            seed += 1
            args.seed += 1

    elif args.mode =='test':
        test(args)

    elif args.mode =='test-behavior':
        testbehavior(args)